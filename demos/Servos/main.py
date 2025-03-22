import os, sys

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend(("../..","../../atlastk.zip"))

import os, io, json, datetime
import ucuq, atlastk

def getGithubFileContent(file_path):
  return ucuq.getWebFileContent(f'https://raw.githubusercontent.com/epeios-q37/ucuq-python/refs/heads/main/{file_path}')

MACRO_MARKER_ = '$'

DEFAULT_SPEED = 10

contentsHidden = True

macros = {}

# Hardware modes
M_STRAIGHT = "Straight"
M_PCA ="PCA"
M_KIT ="Kit"

# Config keys
HARDWARE_KEY = "Hardware"
HARDWARE_MODE_SUBKEY = "Mode"
SPECS_KEY = "Specs"
TWEAK_KEY = "Tweak"

STEP = int(1625 / 180)


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
devices = []


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


KIT_LABELS = {
  "Bipedal": "Freenove/Bipedal/RPiPico(2)W",
  "DIY": "q37.info/DIY/Displays",
  "Dog": "Freenove/Dog/ESP32"
}

def updateFileList(dom, kitLabel = ""):
  html = ""

  for kit in KIT_LABELS:
    html = f"<option value=\"{kit}\" {'selected=\"selected\"' if kit == kitLabel else ''}>{kit}</option>\n" + html

  dom.inner("Files", html)


def atk(dom):
  infos = ucuq.ATKConnect(dom, BODY, True)

  # createCohortServos()

  createServo(ucuq.getDeviceId(infos), ucuq.getDevice(), ucuq.getKitHardware(infos), "")

  displayMacros(dom)
  kitLabel =  ucuq.getKitLabel(infos)

  updateFileList(dom, next((key for key, val in KIT_LABELS.items() if val == kitLabel), None))


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
  device = ""

  with io.StringIO(token[0]) as stream:
    while char := stream.read(1):
      if not char.isalnum():
        raise Exception(f"Servo id expected ({token[1]})!")
      
      servo = char

      char = stream.read(1)

      while char and ( char.isalnum() or char == '_' ):
        servo += char
        char = stream.read(1)

      if char == '.':
        device = servo

        servo += char

        char = stream.read(1)

        while char and ( char.isalnum() or char == '_' ):
          servo += char
          char = stream.read(1)
      else:
        if device != "":
          servo = device + '.' + servo

      if not servo in servos:
        raise Exception(f"No servo of id '{servo}' ({token[1]})")
        
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


  if "_" in macros:
    dom.setValue("Content", macros["_"]["Content"])

  displayMacros(dom)


def handleSetupsKits(setups, kitHardware):
  for setup in setups:
    hardware = setups[setup]["Hardware"]

    if hardware[HARDWARE_MODE_SUBKEY] == M_KIT:
      setups[setup]["Hardware"] = ucuq.getHardware(kitHardware, hardware["Key"], hardware["Index"])

  return setups


def getServosSetups(target, kitHardware):

  with open("servos.json", "r") as file:
    config = json.load(file)[target]



  return handleSetupsKits(config["Servos"], kitHardware)


def createServo(deviceId, device, kitHardware, key):
  global servos

  if key:
    key += '.'

  setups = getServosSetups(deviceId, kitHardware)

  for setup in setups:
    servo = setups[setup]
    hardware = servo[HARDWARE_KEY]
    specs = servo[SPECS_KEY]
    tweak = servo[TWEAK_KEY]
    if ( not HARDWARE_MODE_SUBKEY in hardware ) or hardware[HARDWARE_MODE_SUBKEY] == M_STRAIGHT:
      pwm = ucuq.PWM(hardware["Pin"],device=device, freq=50, u16=0).setNS(0)
      pwm.setFreq(specs["Freq"])
    elif hardware[HARDWARE_MODE_SUBKEY] == M_PCA:
      if not pca:
        i2c = ucuq.SoftI2C if hardware["soft"] else ucuq.I2C
        pca = ucuq.PCA9685(i2c(hardware["sda"], hardware["scl"],device=device))
        pca.setFreq(specs["Freq"])
        pca.setOffset(hardware["Offset"])
      pwm = ucuq.PWM_PCA9685(pca, hardware["channel"])
    else:
      raise Exception("Unknown hardware mode!")

    servos[key+setup] = ucuq.Servo(pwm, ucuq.Servo.Specs(specs["U16Min"], specs["U16Max"], specs["Range"]), tweak = ucuq.Servo.Tweak(tweak["Angle"],tweak["Offset"], tweak["Invert"]))


def createCohortServos():
  global servos
  
  targets = {
    "C": "Charlie",
    "E": "Echo"
  }

  for key in targets:
    createServo(targets[key], ucuq.Device(id=targets[key]), key)

with open('Body.html', 'r') as file:
  BODY = file.read()

with open('Head.html', 'r') as file:
  ATK_HEAD = file.read()

atlastk.launch(globals=globals())

