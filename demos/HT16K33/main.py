import os, sys

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend(("../..","../../atlastk.zip"))

import ucuq, atlastk, binascii

onDuty = False
ht16k33 = None
mirror = None

pattern = "0" * 32

TEST_DELAY = 0.05

def test():
  if ht16k33:
    for y in range(8):
      for x in range(16):
        ht16k33.plot(x,y)
      ht16k33.show()
      ucuq.sleep(TEST_DELAY)
      ht16k33.clear()

    for x in range(16):
      for y in range(8):
        ht16k33.plot(x,y)
      ht16k33.show()
      ucuq.sleep(TEST_DELAY)
      ht16k33.clear()

    for x in range(16):
      for y in range(8):
        ht16k33.plot(x,y)

    ht16k33.show()

    for b in range(0, 16):
      ht16k33.setBrightness(b)
      ucuq.sleep(TEST_DELAY)

    for b in range(15, -1, -1):
      ht16k33.setBrightness(b)
      ucuq.sleep(TEST_DELAY)

    ht16k33.clear().show()


def drawOnGUI(dom, motif = pattern):
  html = ""

  for i, c in enumerate(motif.ljust(32,"0")):
    for o in range(4):
      on = int(c, 16) & (1 << (3 - o)) != 0
      html += f"<div class='led{ '' if on else ' off'}' xdh:onevent='Toggle' data-state='{'on' if on else 'off'}' xdh:mark='{(i % 4) * 4 + o} {i >> 2}'></div>"

  dom.inner("Matrix", html)


def drawLittleMatrix(motif):
  html = ""

  for i, c in enumerate(motif.ljust(32,"0")):
    for o in range(4):
      on = int(c, 16) & (1 << (3 - o)) != 0
      html += f"<div class='little-led{ '' if on else ' little-off'}'></div>"

  return html


def drawLittleMatrices(dom, matrices):
  html = ""

  for i, matrix in enumerate(matrices):
    html += f"<fieldset xdh:mark=\"{i}\" style=\"cursor: pointer;\" class=\"little-matrix\" xdh:onevent=\"Draw\">"\
      + drawLittleMatrix(matrix)\
      +"</fieldset>"

  dom.inner("MatricesBox", html)


def setHexa(dom, motif = pattern):
  dom.setValue("Hexa", motif)


def drawOnMatrix(motif = pattern):
  if ht16k33:
    ht16k33.draw(motif).show()

    if mirror:
      mirror.fill(0).draw(motif, 16, mul=8).show()

def draw(dom, motif = pattern):
  global pattern

  pattern = motif
  
  drawOnMatrix(motif)

  drawOnGUI(dom, motif)

  setHexa(dom, motif)


def updateUI(dom, onDuty):
  ids = ["MatrixBox", "HexaBox", "MiscBox", "MatricesBox"]

  if onDuty:
    dom.enableElements(ids)
    dom.disableElement("HardwareBox")
    dom.setValue("Switch", "true")
  else:
    dom.disableElements(ids)
    dom.enableElement("HardwareBox")
    dom.setValue("Switch", "false")

    match dom.getValue("Preset"):
      case "User":
        dom.enableElements(["SDA", "SCL"])
      case "Bipedal":
        dom.setValues({
          "SDA": 4,
          "SCL": 5
        })
        dom.disableElements(["SDA", "SCL"])
      case _:
        raise Exception("Unknown preset!")
        

def atkConnect(dom):
  id = ucuq.getKitId(ucuq.ATKConnect(dom, BODY))

  draw(dom, "")

  dom.executeVoid("patchHexaInput();")

  drawLittleMatrices(dom,MATRICES)

  if not onDuty:
    if id == ucuq.K_BIPEDAL:
      dom.setValue("Preset", "Bipedal")

  updateUI(dom, onDuty)

def atkPreset(dom, id):
  match dom.getValue("Preset"):
    case "User":
      dom.setValues({
        "SDA": "",
        "SCL": ""
      })
    case "Bipedal":
      pass
    case _:
      raise Exception("Unknown preset!")
    
  updateUI(dom, False)


def launch(dom, sda, scl):
  global ht16k33, onDuty

  try:
    ht16k33 = ucuq.HT16K33(ucuq.I2C(sda, scl))
    ht16k33.clear().show()
    ht16k33.setBrightness(0)
    ht16k33.setBlinkRate(0)
  except Exception as err:
    dom.alert(err)
    onDuty = False
  else:
    onDuty = True


def atkSwitch(dom, id):
  global onDuty

  state = (dom.getValue(id)) == "true"

  if state:
    updateUI(dom, state)

    try:
      sda, scl = (int(value.strip()) for value in (dom.getValues(["SDA", "SCL"])).values())
    except:
      dom.alert("No or bad value for SDA/SCL!")
      updateUI(dom, False)
    else:
      launch(dom, sda, scl)
  else:
    onDuty = False

  updateUI(dom, onDuty)


def atkTest():
  test()


def atkToggle(dom, id):
  if not onDuty:
    dom.alert("Please switch on!")
    return

  global pattern

  [x, y] = list(map(lambda v: int(v), (dom.getMark(id)).split()))

  pos = y * 16 + ( 4 * int(x / 4) + (3 - x % 4)) 

  bin = binascii.unhexlify(pattern.ljust(32,"0")[::-1].encode())[::-1]

  offset = int(pos/8)

  bin = bin[:offset] + bytearray([bin[offset] ^ (1 << (pos % 8))]) + bin[offset+1:]

  pattern = (binascii.hexlify(bin[::-1]).decode()[::-1])

  draw(dom, pattern)


def atkHexa(dom):
  global pattern

  drawOnMatrix(motif := dom.getValue("Hexa"))

  drawOnGUI(dom, motif)

  pattern = motif


def atkAll(dom):
  for matrix in MATRICES:
    draw(dom, matrix)
    ucuq.time.sleep(0.5)


def atkBrightness(dom, id):
  ht16k33.setBrightness(int(dom.getValue(id)))

def atkBlinkRate(dom, id):
  ht16k33.setBlinkRate(float(dom.getValue(id)))

def atkDraw(dom, id):
  draw(dom, MATRICES[int(dom.getMark(id))])

def atkMirror(dom, id):
  global mirror

  state = (dom.getValue(id)) == "true"

  if state:
    if ( dom.confirm("Please do not confirm unless you know exactly what you are doing!") ):
      mirror = ucuq.SSD1306_I2C(128, 64, ucuq.I2C(8, 9, device = ucuq.Device(id="Bravo")))
    else:
      dom.setValue(id, "false")
  else:
    mirror = None
  
MATRICES = (
  "0FF0300C4002866186614002300C0FF",
  "000006000300FFFFFFFF030006",
  "00004002200410080810042003c",
  "0000283810282838000000400040078",
  "081004200ff01bd83ffc2ff428140c3",
  "042003c004200c300ff007e00db",
  "0420024027e42db43ffc18180a50042",
  "0420024007e00ff02bd41ff824241bd8",
  "0300030009c007a0018002600fc0048",
  "08800f800a8007100210079007d00be",
  "02000e000e1003e003e003e00220066",
  "06001a000e000f000ff00fe00f8002",
  "024001800fe01850187018500ff00fe",
  "038004400960041004180408021001e",
  "000003c0042005a005a0042003c",
  "03c0042009900a500a5009e0040803f",
  "239f6441204223862401241177ce",
  "43dc421242124392421242127bdc",
  "00003c3c727272727e7e7e7e3c3c",
  "00003ffc40025ffa2ff417e8081007e",
)


with open('Body.html', 'r') as file:
  BODY = file.read()

with open('Head.html', 'r') as file:
  HEAD = file.read()

atlastk.launch(CALLBACKS if "CALLBACKS" in globals() else None, globals=globals(), headContent=HEAD, userCallback = USER if "USER" in globals() else None)

