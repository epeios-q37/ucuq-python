import os, sys

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend(("../..","../../atlastk.zip"))

import os, io, json, datetime
import ucuq, atlastk


MACRO_MARKER_ = '$'

DEFAULT_SPEED = 10

contentsHidden = True

macros = {}

# Hardware modes
M_STRAIGHT = "Straight"
M_PCA ="PCA"

# Config keys
HARDWARE_KEY = "Hardware"
HARDWARE_MODE_SUBKEY = "mode"
SPECS_KEY = "Specs"
TWEAK_KEY = "Tweak"

STEP = int(1625 / 180)

CONFIG_KEYS = {
  HARDWARE_KEY: {
    M_STRAIGHT: ["pin"],
    M_PCA: ["sda", "scl", "channel", "offset", "soft"]
  },
  SPECS_KEY: ["freq", "u16_min", "u16_max", "range"],
  TWEAK_KEY: ["angle", "offset", "invert"]
}

MACRO_HTML="""
<div class="macro" xdh:mark="Macro{}" style="margin-bottom: 3px;">
  <label>
    <span>Name:&nbsp;</span>
    <input disabled="disabled" value="{}">
  </label>
  <label>
    <span>Desc.:&nbsp;</span>
    <input disabled="disabled" value="{}">
  </label>
  <div>
    <button xdh:onevent="Execute">Execute</button>
  </div>
  <textarea class="description" disabled="disabled">{}</textarea>
  <div class="description">
    <button xdh:onevent="Edit">Edit</button>
    <button xdh:onevent="Delete">Delete</button>
  </div>
</div>
"""

servos = {}
pca = None


def reset_():
  moves = []
  for servo in servos.values():
    moves.append([servo, 0])

  ucuq.servoMoves(moves, int(2 * STEP * DEFAULT_SPEED))


def displayMacros(dom):
  html = "<legend>Macros</legend><div>"

  if len(macros) >= 1:
    for macro in macros:
      if macro != '_':
        html += MACRO_HTML.format(macro, macro, macros[macro]["Description"], macros[macro]["Content"])
  else:
    html += "<em>No macros available</em>"

  html += "</div>"

  dom.inner("Macros", html)


MACROS = {
  "Bipedal": ucuq.K_BIPEDAL,
  "DIY": ucuq.K_DIY_SERVOS,
  "Dog": ucuq.K_DOG
}

def updateFileList(dom, kit = ucuq.K_UNKNOWN):
  html = ""
  for macro in MACROS:
    html = f"<option value=\"{macro}\" {'selected=\"selected\"' if MACROS[macro] == kit else ''}>{macro}</option>\n" + html

  dom.inner("Files", html)


def atkConnect(dom):
  infos = ucuq.ATKConnect(dom, BODY)

  createServos(ucuq.getDeviceId(infos))

  displayMacros(dom)
  updateFileList(dom, ucuq.getKitId(infos))


def atkTest():
  reset_()
  step = int(STEP * DEFAULT_SPEED / 2)
  for servo in servos:
    ucuq.servoMoves([[servos[servo], 15]], step)
    ucuq.servoMoves([[servos[servo], -15]], step)
    ucuq.servoMoves([[servos[servo], 0]], step)
  

def atkReset(dom):
  reset_()


def getToken(stream):
  token = ""

  char = stream.read(1)

  while char and char == ' ':
    char = stream.read(1)

  pos = stream.tell()

  while char and char != ' ':
    token += char
    char = stream.read(1)

  if token:
    return (token, pos)
  else:
    return None
  

def getMacro(token):
  name = ""
  amount = 1

  with io.StringIO(token[0]) as stream:
    if not ( char := stream.read(1) ):
      raise Exception(f"Unexpected error ({token[1]})!")
    
    if char.isdigit():
      amount = int(char)

      while ( char := stream.read(1) ) and char .isdigit():
        amount = amount * 10 + int(char)

    if char != MACRO_MARKER_:
      raise Exception(f"Missing macro reference ({token[1]})!")
    
    if not (char := stream.read(1)):
      raise Exception(f"Empty macro name ({token[1]})!")
    
    if not char.isalpha(): 
      raise Exception(f"Macro name must beginning with a letter ({token[1]})!")
    
    while char and char.isalnum():
      name += char
      char = stream.read(1)

    if char:
      raise Exception(f"Unexpected character after macro call ({token[1]})!")

  if not name in macros:
    raise Exception(f"Unknown macro ({token[1]})!")

  return {"name": name, "amount" :amount} 


def getMoves(token):
  moves = []
  speed = None

  with io.StringIO(token[0]) as stream:
    while char := stream.read(1):
      if not char.isalnum():
        raise Exception(f"Servo id expected ({token[1]})!")
      
      servo = char

      char = stream.read(1)

      while char and ( char.isalnum() or char == '_' ):
        servo += char
        char = stream.read(1)

      if not servo in servos:
        raise Exception(f"No servo of id '{servo}'  ({token[1]})")
        
      angle = 0
      sign = 1

      if char:
        if char in "+-":
          if char == '-':
            sign = -1
          char = stream.read(1)


      while char and char.isdigit():
        angle = angle * 10 + int(char)
        char = stream.read(1)

      moves.append((servos[servo], angle * sign))

      if not char:
        break

      if char != "%":
        if char != ':':
          raise Exception(f"Servo move can only be followed by '%' ({token[1]})!")
      else:
        speed = ""

        while (char := stream.read(1)) and char.isdigit():
          speed += char

        if char:
          raise Exception(f"Unexpected char at end of servo moves ({token[1]})!")
        
    return { "moves": moves, "speed": speed}
  

def getSpeed(token):
  speed = 0

  with io.StringIO(token[0]) as stream:
    if stream.read(1) != '%':
      raise Exception(f"Unexpected error ({token[1]})!")
    
    while (char := stream.read(1)) and char.isdigit():
      speed = speed * 10 + int(char)

  return { "value": speed if speed else DEFAULT_SPEED }


def tokenize(string):
  tokens = []

  with io.StringIO(string) as stream:
    while token := getToken(stream):
      tokens.append(token)

  return tokens


def getAST(tokens):
  ast = []
  for token in tokens:
    if token[0][0].isdigit() or token[0][0] == MACRO_MARKER_:
      ast.append(("macro", getMacro(token)))
    elif token[0][0] == '%':
      ast.append(("speed", getSpeed(token)))
    else:
      ast.append(("action",getMoves(token)))

  return ast


def execute(dom, string, speed = DEFAULT_SPEED):
  try:
    ast = getAST(tokenize(string))

    for item in ast:
      match item[0]:
        case "action":
          tempSpeed = item[1]["speed"]
          ucuq.servoMoves(item[1]["moves"], int(STEP * ( speed if tempSpeed == None else ( int(tempSpeed) if tempSpeed != "" else DEFAULT_SPEED))))
        case "macro":
          for _ in range(item[1]["amount"]):
            execute(dom, macros[item[1]["name"]]["Content"], speed)
        case "speed":
          speed = item[1]["value"]
  except Exception as err:
    dom.alert(err)


def atkExecute(dom, id):
  mark = dom.getMark(id)

  if mark == "Buffer":
    moves = dom.getValue("Content")
    dom.focus("Content")
  else:
    moves = macros[mark[5:]]["Content"]

  if dom.getValue("Reset") == "true":
    reset_()

  execute(dom, moves)


def atkSave(dom):

  name = dom.getValue("Name").strip()

  if not ( content := dom.getValue("Content") ):
    dom.alert("There is no content to save!")
  else:
    macros["_"] = {"Description": "Internal use", "Content": content}

    if name == "":
        dom.alert("Please give a name for the macro!")
    elif not name.isidentifier() or name == '_':
      dom.alert(f"'{name}' is not a valid macro name!")
    elif not name in macros or dom.getValue("Ask") == "true" or dom.confirm(f"Overwrite existing macro of name '{name}'?"):
      macros[name] = {"Description": dom.getValue("Description"), "Content": content}

      with open(f"Macros/Latest.json", "w") as file: 
        file.write(json.dumps(macros, indent=2)) # type: ignore

    displayMacros(dom)

def expand(moves):
  content = ""
  
  for item in getAST(tokenize(moves)):
    match item[0]:
      case 'action':
        for move in item[1]["moves"]:
          content += move[0] + move[1] + ":"
        content = content[:-1]
        if item[2]:
          content += f"%{item[2]}"
        content += " "
      case 'macro':
        if not ( name := item[1]["name"] ) in macros:
          raise Exception(f"No macro named '{item[1]}!")
        else:
          for _ in range(item[1]["amount"]):
            content += macros[item[1]["name"]]["Content"] + " "

  return content


def atkExpand(dom):
  try:
    dom.setValue("Content", expand(dom.getContent("Content")))
  except Exception as err:
    dom.alert(err)


def atkDelete(dom, id):
  name = (dom.getMark(id))[5:]

  if dom.confirm(f"Delete macro '{name}'?"):
    del macros[name]
    displayMacros(dom)


def atkEdit(dom, id):
  name = (dom.getMark(id))[5:]

  dom.setValues({
    "Name": name,
    "Description": macros[name]["Description"],
    "Content": macros[name]["Content"],
    "Ask": "false"
  })


def atkHideContents(dom):
  global contentsHidden

  contentsHidden = not contentsHidden

  if contentsHidden:
    dom.enableElement("HideContents")
  else:
    dom.disableElement("HideContents")

  
def atkSaveToFile(dom):

  with open(f"Macros/{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json", "w") as file: 
    file.write(json.dumps(macros, indent=2)) # type: ignore
  
  updateFileList(dom)

def atkLoadFromFile(dom):
  global macros

  with open(f"Macros/{dom.getValue('Files')}.json", "r") as file:
    macros = json.load(file)


  print("Macros: ", macros)

  if "_" in macros:
    dom.setValue("Content", macros["_"]["Content"])

  displayMacros(dom)


command = ""

def getSetupDefaultValue(key, subkey):
  if key == HARDWARE_KEY:
    if subkey == "offset":
      return 0
    elif subkey == "soft":
      return False
  elif key == TWEAK_KEY:
    if subkey in ["angle", "offset"]:
      return 0
    elif subkey == "invert":
      return False
  
  raise Exception(f"Missing value for '{key}/{subkey}' in servos setup file!")


def getServoSetup(key, subkey, preset, motor):
  if ( key in motor ) and ( subkey in motor[key] ):
    return motor [key][subkey]
  elif subkey in preset[key]:
    return preset[key][subkey]
  else:
    return getSetupDefaultValue(key, subkey)


def getServosSetups(target):
  setups = {}


  with open("servos.json", "r") as file:
    config = json.load(file)[target]



  preset = config["Preset"]
  motors = config["Motors"]

  for label in motors:
    setups[label] = {}

    motor = motors[label]

    for key in CONFIG_KEYS:
      setups[label][key] = {}

      if key == HARDWARE_KEY:
        mode = getServoSetup(key, HARDWARE_MODE_SUBKEY, motor, preset)

        setups[label][key][HARDWARE_MODE_SUBKEY] = mode

        for subkey in CONFIG_KEYS[key][mode]:
          setups[label][key][subkey] = getServoSetup(key, subkey, preset, motor)
      else:
        for subkey in CONFIG_KEYS[key]:
          setups[label][key][subkey] = getServoSetup(key, subkey, preset, motor)

  return setups

def createServos(deviceId):
  global servos, pca

  setups = getServosSetups(deviceId)

  for setup in setups:
    servo = setups[setup]
    hardware = servo[HARDWARE_KEY]
    specs = servo[SPECS_KEY]
    tweak = servo[TWEAK_KEY]
    if hardware[HARDWARE_MODE_SUBKEY] == M_STRAIGHT:
      pwm = ucuq.PWM(hardware["pin"])
      pwm.setFreq(specs["freq"])
    elif hardware["mode"] == "PCA":
      if not pca:
        i2c = ucuq.SoftI2C if hardware["soft"] else ucuq.I2C
        pca = ucuq.PCA9685(i2c(hardware["sda"], hardware["scl"]))
        pca.setFreq(specs["freq"])
        pca.setOffset(hardware["offset"])
      pwm = ucuq.PWM_PCA9685(pca, hardware["channel"])
    else:
      raise Exception("Unknown hardware mode!")
    servos[setup] = ucuq.Servo(pwm, ucuq.Servo.Specs(specs["u16_min"], specs["u16_max"], specs["range"]), tweak = ucuq.Servo.Tweak(tweak["angle"],tweak["offset"], tweak["invert"]))

with open('Body.html', 'r') as file:
  BODY = file.read()

with open('Head.html', 'r') as file:
  HEAD = file.read()

atlastk.launch(CALLBACKS if "CALLBACKS" in globals() else None, globals=globals(), headContent=HEAD, userCallback = USER if "USER" in globals() else None)

