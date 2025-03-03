import os, sys

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend(("../..","../../atlastk.zip"))

import atlastk, ucuq, random, json

RB_DELAY = .05

ws2812 = None
ws2812Limiter = 0
onDuty = False
oledDIY = None

# Presets
P_USER = "User"
P_BIPEDAL = "Bipedal"
P_DOG = "Dog"
P_DIY = "DIY"
P_WOKWI = "Wokwi"

SPOKEN_COLORS =  {
  "rouge": [255, 0, 0],
  "vert": [0, 255, 0],
  "verre": [0, 255, 0],
  "verte": [0, 255, 0],
  "bleu": [0, 0, 255],
  "jaune": [255, 255, 0],
  "cyan": [0, 255, 255],
  "magenta": [255, 0, 255],
  "orange": [255, 127, 0],
  "violet": [127, 0, 255],
  "rose": [255, 127, 127],
  "gris": [127, 127, 127],
  "noir": [0, 0, 0],
  "blanc": [255, 255, 255],
  "marron": [127, 59, 0],
  "turquoise": [0, 127, 127],
  "beige": [255, 212, 170]
}


def rainbow():
  v =  random.randint(0, 5)
  i = 0
  while i < 7 * ws2812Limiter:
    ws2812.fill(ucuq.rbShadeFade(v, int(i), ws2812Limiter)).write()
    ucuq.sleep(RB_DELAY)
    i += ws2812Limiter / 20
  ws2812.fill([0]*3).write()


def convert_(hex):
  return int(int(hex,16) * 100 / 256)


def getValues_(target, R, G, B):
  return {
    target + "R": R,
    target + "G": G,
    target + "B": B
  }


def getNValues_(R, G, B):
  return getValues_("N", R, G, B)


def getSValues_(R, G, B):
  return getValues_("S", R, G, B)


def getAllValues_(R, G, B):
  return getNValues_(R, G, B) | getSValues_(R, G, B)


def update_(r, g, b):
  if ws2812:
    ws2812.fill([int(r), int(g), int(b)]).write()
    if oledDIY:
      oledDIY.fill(0).text(f"R: {r}", 0, 5).text(f"G: {g}", 0, 20).text(f"B: {b}", 0, 35).show()


def launch(dom, pin, count):
  global ws2812, onDuty

  try:
    ws2812 = ucuq.WS2812(pin, count)
  except Exception as err:
    dom.alert(err)
    onDuty = False
  else:
    onDuty = True


def reset(dom):
  dom.executeVoid(f"colorWheel.rgb = [0, 0, 0]")
  dom.setValues(getAllValues_(0, 0, 0))
  update_(0, 0, 0)    


def updateUI(dom, onDuty):
  ids = ["SlidersBox", "PickerBox"]

  if onDuty:
    dom.enableElements(ids)
    dom.disableElements(["HardwareBox", "Preset"])
    dom.setValue("Switch", "true")
  else:
    dom.disableElements(ids)
    dom.enableElements(["HardwareBox", "Preset"])
    dom.setValue("Switch", "false")

    preset = dom.getValue("Preset")

    if preset == P_BIPEDAL:
      dom.setValues({
        "Pin": ucuq.H_BIPEDAL["RGB"]["Pin"],
        "Count": ucuq.H_BIPEDAL["RGB"]["Count"],
        "Offset": ucuq.H_BIPEDAL["RGB"]["Offset"],
        "Limiter": ucuq.H_BIPEDAL["RGB"]["Limiter"],
      })
    elif preset == P_DOG:
      dom.setValues({
        "Pin": ucuq.H_DOG["RGB"]["Pin"],
        "Count": ucuq.H_DOG["RGB"]["Count"],
        "Offset": ucuq.H_DOG["RGB"]["Offset"],
        "Limiter": ucuq.H_DOG["RGB"]["Limiter"],
      })
    elif preset == P_DIY:
      dom.setValues({
        "Pin": ucuq.H_DIY_DISPLAYS["Ring"]["Pin"],
        "Count": ucuq.H_DIY_DISPLAYS["Ring"]["Count"],
        "Offset": ucuq.H_DIY_DISPLAYS["Ring"]["Offset"],
        "Limiter": ucuq.H_DIY_DISPLAYS["Ring"]["Limiter"],
      })
    elif preset == P_WOKWI:
      dom.setValues({
        "Pin": ucuq.H_WOKWI_DISPLAYS["Ring"]["Pin"],
        "Count": ucuq.H_WOKWI_DISPLAYS["Ring"]["Count"],
        "Offset": ucuq.H_WOKWI_DISPLAYS["Ring"]["Offset"],
        "Limiter": ucuq.H_WOKWI_DISPLAYS["Ring"]["Limiter"],
      })
    elif preset != P_USER:
      raise Exception("Unknown preset!")


def atkConnect(dom):
  global oledDIY
  id = ucuq.getKitId(ucuq.ATKConnect(dom, BODY))

  dom.executeVoid("setColorWheel()")
  dom.executeVoid(f"colorWheel.rgb = [0, 0, 0]")

  if not onDuty:
    if id == ucuq.K_BIPEDAL:
      dom.setValue("Preset", P_BIPEDAL)
    elif id == ucuq.K_DOG:
      dom.setValue("Preset", P_DOG)
    elif id == ucuq.K_DIY_DISPLAYS:
      oledDIY = ucuq.SSD1306_I2C(128, 64, ucuq.I2C(ucuq.H_DIY_DISPLAYS["OLED"]["SDA"], ucuq.H_DIY_DISPLAYS["OLED"]["SCL"], soft = ucuq.H_DIY_DISPLAYS["OLED"]["Soft"]))
      dom.setValue("Preset", P_DIY)
    elif id == ucuq.K_WOKWI_DISPLAYS:
      oledDIY = ucuq.SSD1306_I2C(128, 64, ucuq.I2C(ucuq.H_WOKWI_DISPLAYS["OLED"]["SDA"], ucuq.H_WOKWI_DISPLAYS["OLED"]["SCL"], soft = ucuq.H_WOKWI_DISPLAYS["OLED"]["Soft"]))
      dom.setValue("Preset", P_WOKWI)

  updateUI(dom, False)


def atkPreset(dom):
  updateUI(dom, onDuty)


def atkSwitch(dom, id):
  global onDuty, ws2812Limiter

  state = (dom.getValue(id)) == "true"

  if state:
    updateUI(dom, state)

    try:
      pin, count, ws2812Limiter = (int(value.strip()) for value in (dom.getValues(["Pin", "Count", "Limiter"])).values())
    except:
      dom.alert("No or bad value for Pin/Count!")
      updateUI(dom, False)
    else:
      launch(dom, pin, count)
  else:
    onDuty = False

  updateUI(dom, onDuty)


def atkSelect(dom):
  if onDuty:
    R, G, B = (dom.getValues(["rgb-r", "rgb-g", "rgb-b"])).values()
    dom.setValues(getAllValues_(R, G, B))
    update_(R, G, B)
  else:
    dom.executeVoid(f"colorWheel.rgb = [0,0,0]")  


def atkSlide(dom):
  (R,G,B) = (dom.getValues(["SR", "SG", "SB"])).values()
  dom.setValues(getNValues_(R, G, B))
  dom.executeVoid(f"colorWheel.rgb = [{R},{G},{B}]")
  update_(R, G, B)


def atkAdjust(dom):
  (R,G,B) = (dom.getValues(["NR", "NG", "NB"])).values()
  dom.setValues(getSValues_(R, G, B))
  dom.executeVoid(f"colorWheel.rgb = [{R},{G},{B}]")
  update_(R, G, B)


def atkListen(dom):
  dom.executeVoid("launch()")

  
def atkDisplay(dom):
  colors = json.loads(dom.getValue("Color"))

  for color in colors:
    color = color.lower()
    if color in SPOKEN_COLORS:
      r, g, b = [ws2812Limiter * c // 255 for c in SPOKEN_COLORS[color]]
      dom.setValues(getAllValues_(r, g, b))
      dom.executeVoid(f"colorWheel.rgb = [{r},{g},{b}]")
      update_(r, g, b)
      if oledDIY:
        oledDIY.text(color, 0, 50).show()
      break


def atkRainbow(dom):
  reset(dom)
  rainbow()


def atkReset(dom):
  reset(dom)


with open('Body.html', 'r') as file:
  BODY = file.read()

with open('Head.html', 'r') as file:
  HEAD = file.read()

atlastk.launch(CALLBACKS if "CALLBACKS" in globals() else None, globals=globals(), headContent=HEAD, userCallback = USER if "USER" in globals() else None)

