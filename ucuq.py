###########################
#      DO NOT MODIFY      #
# COMPUTER GENERATED FILE #
###########################

import os, json, socket, sys, threading, datetime, time
from inspect import getframeinfo, stack

CONFIG_FILE = ( "/home/csimon/q37/epeios/tools/ucuq/remote/wrappers/PYH/" if "Q37_EPEIOS" in os.environ else "../" ) + "ucuq.json"

try:
  with open(CONFIG_FILE, "r") as config:
    CONFIG = json.load(config)
except:
  CONFIG = None

UCUQ_DEFAULT_HOST_ = "ucuq.q37.info"
UCUQ_DEFAULT_PORT_ = "53800"

UCUQ_HOST_ = CONFIG["Proxy"]["Host"] if CONFIG and "Proxy" in CONFIG and "Host" in CONFIG["Proxy"] and CONFIG["Proxy"]["Host"] else UCUQ_DEFAULT_HOST_

# only way to test if the entry contains a valid int.
try:
  UCUQ_PORT_ = int(CONFIG["Proxy"]["Port"])
except:
  UCUQ_PORT_ = int(UCUQ_DEFAULT_PORT_)

PROTOCOL_LABEL_ = "c37cc83e-079f-448a-9541-5c63ce00d960"
PROTOCOL_VERSION_ = "0"

uuid_ = 0
device_ = None
_writeLock = threading.Lock()

ITEMS_ = "i_"

# Request
R_EXECUTE_ = "Execute_1"
R_UPLOAD_ = "Upload_1"

# Answer
A_OK_ = 0
A_ERROR_ = 1
A_PUZZLED_ = 2
A_DISCONNECTED = 3

def GetUUID_():
  global uuid_

  uuid_ += 1

  return uuid_

def recv_(socket, size):
  buffer = bytes()
  l = 0

  while l != size:
    buffer += socket.recv(size-l)
    l = len(buffer)

  return buffer


def send_(socket, value):
  totalAmount = len(value)
  amountSent = 0

  while amountSent < totalAmount:
    amountSent += socket.send(value[amountSent:])


def writeUInt_(socket, value):
  result = bytes([value & 0x7f])
  value >>= 7

  while value != 0:
    result = bytes([(value & 0x7f) | 0x80]) + result
    value >>= 7

  send_(socket, result)


def writeString_(socket, string):
  bString = bytes(string, "utf-8")
  writeUInt_(socket, len(bString))
  send_(socket, bString)


def writeStrings_(socket, strings):
  writeUInt_(socket, len(strings))

  for string in strings:
    writeString_(socket, string)


def readByte_(socket):
  return ord(recv_(socket, 1))


def readUInt_(socket):
  byte = readByte_(socket)
  value = byte & 0x7f

  while byte & 0x80:
    byte = readByte_(socket)
    value = (value << 7) + (byte & 0x7f)

  return value


def readString_(socket):
  size = readUInt_(socket)

  if size:
    return recv_(socket, size).decode("utf-8")
  else:
    return ""


def exit_(message=None):
  if message:
    print(message, file=sys.stderr)
  sys.exit(-1)


def init_():
  s = socket.socket()

  print("Connection to UCUq server…", end="", flush=True)

  try:
    s.connect((UCUQ_HOST_, UCUQ_PORT_))
  except Exception as e:
    raise e
  else:
    print("\r                                         \r",end="")

  return s


def handshake_(socket):
  with _writeLock:
    writeString_(socket, PROTOCOL_LABEL_)
    writeString_(socket, PROTOCOL_VERSION_)
    writeString_(socket, "Remote")
    writeString_(socket, "PYH")

  error = readString_(socket)

  if error:
    sys.exit(error)

  notification = readString_(socket)

  if notification:
    pass
    # print(notification)


def ignition_(socket, token, deviceId, errorAsException):
  writeString_(socket, token)
  writeString_(socket, deviceId)

  error = readString_(socket)

  if error:
    if errorAsException:
      raise Error(error)
    else:
      return False
    
  return True


def connect_(token, deviceId, errorAsException):
  socket = init_()
  handshake_(socket)
  if ignition_(socket, token, deviceId, errorAsException):
    return socket
  else:
    return None


class Error(Exception):
  pass

def commit(expression=""):
  return getDevice_().commit(expression)

def sleep(secs):
  return getDevice_().sleep(secs)

def displayExitMessage_(Message):
  raise Error(Message)


class Device_:
  def __init__(self, *, id = None, token = None):
    self.socket_ = None

    if id or token:
      self.connect(id, token)

  def connect(self, id = None, token = None, errorAsException = True):
    if token == None and id == None:
      token, id = handlingConfig_(token, id)

    self.token = token if token else "%DEFAULT_VTOKEN%"
    self.id = id if id else ""

    self.socket_ = connect_(self.token, self.id, errorAsException = errorAsException)

    return self.socket_ != None

  def upload(self, modules):
    writeString_(self.socket_, R_UPLOAD_)
    writeStrings_(self.socket_, modules)

    if ( answer := readUInt_(self.socket_) ) == A_OK_:
      readString_(self.socket_) # For future use
    elif answer == A_ERROR_:
      result = readString_(self.socket_)
      print(f"\n>>>>>>>>>> ERROR FROM DEVICE BEGIN <<<<<<<<<<")
      print("Timestamp: ", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') )
      caller = getframeinfo(stack()[1][0])
      print(f"Caller: {caller.filename}:{caller.lineno}")
      print(f">>>>>>>>>> ERROR FROM DEVICE CONTENT <<<<<<<<<<")
      print(result)
      print(f">>>>>>>>>> END ERROR FROM DEVICE END <<<<<<<<<<")
      sys.exit(0)
    elif answer == A_PUZZLED_:
      readString_(self.socket_) # For future use
      raise Error("Puzzled!")
    elif answer == A_DISCONNECTED:
        raise Error("Disconnected from device!")
    else:
      raise Error("Unknown answer from device!")


  def execute_(self, script, expression = ""):
    if self.socket_:
      writeString_(self.socket_, R_EXECUTE_)
      writeString_(self.socket_, script)
      writeString_(self.socket_, expression)

      if ( answer := readUInt_(self.socket_) ) == A_OK_:
        if result := readString_(self.socket_):
          return json.loads(result)
        else:
          return None
      elif answer == A_ERROR_:
        result = readString_(self.socket_)
        print(f"\n>>>>>>>>>> ERROR FROM DEVICE BEGIN <<<<<<<<<<")
        print("Timestamp: ", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') )
        caller = getframeinfo(stack()[1][0])
        print(f"Caller: {caller.filename}:{caller.lineno}")
        print(f">>>>>>>>>> ERROR FROM DEVICE CONTENT <<<<<<<<<<")
        print(result)
        print(f">>>>>>>>>> END ERROR FROM DEVICE END <<<<<<<<<<")
        sys.exit(0)
      elif answer == A_PUZZLED_:
        readString_(self.socket_) # For future use
        raise Error("Puzzled!")
      elif answer == A_DISCONNECTED:
          raise Error("Disconnected from device!")
      else:
        raise Error("Unknown answer from device!")


class Device(Device_):
  def __init__(self, *, id = None, token = None):
    self.pendingModules = ["Init-1"]
    self.handledModules = []
    self.commands = []

    super().__init__(id = id, token = token)

  def addModule(self, module):
    if not module in self.pendingModules and not module in self.handledModules:
      self.pendingModules.append(module)

  def addModules(self, modules):
    if isinstance( modules, str):
      self.addModule(modules)
    else:
      for module in modules:
        self.addModule(module)

  def addCommand(self, command):
    self.commands.append(command)

  def commit(self, expression = ""):
    result = ""

    if self.pendingModules:
      super().upload(self.pendingModules)
      self.handledModules.extend(self.pendingModules)
      self.pendingModules = []

    if self.commands or expression:
      result = super().execute_('\n'.join(self.commands), expression)
      self.commands = []

    return result
  
  def sleep(self, secs):
    self.addCommand(f"time.sleep({secs})")
    

def findDevice(dom):
  for deviceId in VTOKENS:
    dom.inner("", f"<h3>Connecting to '{deviceId}'…</h3>")

    device = Device()

    if device.connect(token = VTOKENS[deviceId], id=deviceId, errorAsException = False):
      return device
  
  return None   

###############
# COMMON PART #
###############


# Keys
K_DEVICE = "Device"
K_DEVICE_TOKEN = "Token"
K_DEVICE_ID = "Id"

VTOKENS = {
    "Black": "e8c3d4f9-9f3a-4abe-ace7-1b2c3f4e5a67",
    "White": "c29f8a92-5f1e-4b4e-bd8b-8b4e0f2c3d19",
    "Yellow": "4e5b8f3b-1f8c-42f1-bcd4-5c9d3b1e9e12",
    "Red": "6c1e5ef5-a69f-4b7b-9e3b-1f23a6c7b3c8",
    "Blue": "ab9e1e8e-42b1-4a5f-8d5a-bb2f0f29a6c0",
    "Striped": "8f7d3f6c-2f1e-4fa4-9b9d-8c5e4f0a8c06",
}

ALL_DEVICES_VTOKEN = "84210c27-cdf8-438f-8641-a2e12380c2cf"


def displayMissingConfigMessage_():
  displayExitMessage_("Please launch the 'Config' app first to set the device to use!")


def handlingConfig_(token, id):
  if not CONFIG:
    displayMissingConfigMessage_()

  if K_DEVICE not in CONFIG:
    displayMissingConfigMessage_()

  device = CONFIG[K_DEVICE]

  if not token:
    if K_DEVICE_TOKEN not in device:
      displayMissingConfigMessage_()

    token = device[K_DEVICE_TOKEN]

  if not id:
    if K_DEVICE_ID not in device:
      displayMissingConfigMessage_()

    id = device[K_DEVICE_ID]

  return token, id


def setDevice(id = None, *, device = None, token = None):
  if device != None:
    global device_
    if id or token:
      raise Exception("'device' can not be given together with 'id' or 'token'!")
    device_ = device
  else:    
    getDevice_(id = id, token = token)


# Infos keys and subkeys
I_KITS_KEY = "Kits"
I_KIT_KEY = "Kit"
I_DEVICE_KEY = "Device"
I_DEVICE_ID_KEY = "Id"
I_DEVICE_UNAME_KEY = "uname"
I_KIT_BRAND_KEY = "brand"
I_KIT_MODEL_KEY = "model"
I_KIT_VARIANT_KEY = "variant"
I_KIT_LABEL_KEY = "label"
I_UNAME_KEY = "uname"


INFO_SCRIPT_ = f"""
def ucuqGetKit():
  try:
    return CONFIG_["{I_KIT_KEY}"]
  except:
    try:
      return CONFIG_["{I_KITS_KEY}"][getIdentificationId_(IDENTIFICATION_)]
    except:
      return None

def ucuqStructToDict(obj):
    return {{attr: getattr(obj, attr) for attr in dir(obj) if not attr.startswith('__')}}

def ucuqGetInfos():
  return {{
    "{I_DEVICE_KEY}" : {{
      "{I_DEVICE_ID_KEY}": getIdentificationId_(IDENTIFICATION_),
      "{I_DEVICE_UNAME_KEY}": ucuqStructToDict(uos.uname())
    }},
    "{I_KIT_KEY}": ucuqGetKit(),
  }}
"""

ATK_STYLE = """
<style>
.ucuq {
  max-height: 200px;
  overflow: hidden;
  opacity: 1;
  animation: ucuqFadeOut 2s forwards;
}

@keyframes ucuqFadeOut {
  0% {
    max-height: 200px;
  }
  100% {
    max-height: 0;
  }
}
</style>
"""

ATK_BODY = """
<div style="display: flex; justify-content: center;" class="ucuq">
  <h3>'{}'</h3>
</div>
<div id="ucuq_body">
</div>
"""

# Handled kits.
K_UNKNOWN = 0
K_BIPEDAL = 1
K_DOG = 2
K_DIY_DISPLAYS = 3
K_DIY_SERVOS = 4
K_WOKWI_DISPLAYS = 5
K_WOKWI_SERVOS = 6

KITS_ = {
  "Freenove/Bipedal/RPiPicoW": K_BIPEDAL,
  "Freenove/Dog/ESP32": K_DOG,
  "q37.info/DIY/Displays": K_DIY_DISPLAYS,
  "q37.info/DIY/Servos": K_DIY_SERVOS,
  "q37.info/Wokwi/Displays": K_WOKWI_DISPLAYS,
  "q37.info/Wokwi/Servos": K_WOKWI_SERVOS,
}

def getInfos(device = None):
  device = getDevice_(device)

  device.addCommand(INFO_SCRIPT_)

  return device.commit("ucuqGetInfos()")


def getKitLabel(infos):
  kit = infos[I_KIT_KEY]

  if kit:
    return f"{kit[I_KIT_BRAND_KEY]}/{kit[I_KIT_MODEL_KEY]}/{kit[I_KIT_VARIANT_KEY]}"
  else:
    return "Undefined"


def getKitId(infos):
  label = getKitLabel(infos)

  if label in KITS_:
    return KITS_[label]
  else:
    return K_UNKNOWN
  

def getDeviceId(infos):
  return infos[I_DEVICE_KEY][I_DEVICE_ID_KEY]
  

def ATKConnect(dom, body, *, device = None):
  dom.inner("", "<h3>Connecting…</h3>")
  
  if device or CONFIG:
    dom.inner("", "<h3>Connecting…</h3>")
    device = getDevice_(device)
  else:
    device = findDevice(dom)

  if not device:
    dom.inner("", "<h3>ERROR: Please launch the 'Config' application!</h3>")
    raise SystemExit("Unable to connect to a device!")
  else:
    setDevice(device = device)
    infos = getInfos(device)
  
  dom.inner("", ATK_BODY.format(getKitLabel(infos)))

  dom.inner("ucuq_body", body)

  time.sleep(0.5)

  dom.begin("", ATK_STYLE)

  time.sleep(1.5)

  dom.inner("", body)

  return infos


def getDevice_(device = None, *, id = None, token = None):
  if device and ( token or id):
    displayExitMessage_("'device' can not be given together with 'token' or 'id'!")

  if device == None:
    global device_

    if token or id:
      device_ = Device(id = id, token = token)
    elif device_ == None:
      device_ = Device()
      device_.connect()
    
    return device_
  else:
    return device


def addCommand(command, /,device = None):
  getDevice_(device).addCommand(command)


# does absolutely nothing whichever method is called.
class Nothing:
  def __getattr__(self, name):
    def doNothing(*args, **kwargs):
      return self
    return doNothing


class Core_:
  def __init__(self, device = None):
    self.id = None
    self.device_ = device
  
  def __del__(self):
    if self.id:
      self.addCommand(f"del {ITEMS_}[{self.id}]")

  def getDevice(self):
    return self.device_
  
  def init(self, modules, instanciation, device):
    self.id = GetUUID_()

    if self.device_:
        if device and device != self.device_:
          raise Exception("'device' already given!")
    else:
      self.device_ = getDevice_(device)

    if modules:
      self.device_.addModules(modules)

    if instanciation:
      self.addCommand(f"{self.getObject()} = {instanciation}")

  def getObject(self):
    return f"{ITEMS_}[{self.id}]"

  def addCommand(self, command):
    self.device_.addCommand(command)

    return self

  def addMethods(self, methods):
    return self.addCommand(f"{self.getObject()}.{methods}")

  def callMethod(self, method):
    return self.device_.commit(f"{self.getObject()}.{method}")
                         

class GPIO(Core_):
  def __init__(self, pin = None, device = None):
    super().__init__(device)

    if pin:
      self.init(pin, device)

  def init(self, pin, device = None):
    self.pin = f'"{pin}"' if isinstance(pin,str) else pin

    super().init("GPIO-1", f"GPIO({self.pin})", device)


  def high(self, value = True):
    self.addMethods(f"high({value})")


  def low(self):
    self.high(False)


class WS2812(Core_):
  def __init__(self, pin = None, n = None, device = None):
    super().__init__(device)

    if (pin == None) != (n == None):
      raise Exception("Both or none of 'pin'/'n' must be given")

    if pin != None:
      self.init(pin, n)

  def init(self, pin, n, device = None):
    super().init("WS2812-1", f"neopixel.NeoPixel(machine.Pin({pin}), {n})", device)

  def len(self):
    return int(self.callMethod("__len__()"))
               

  def setValue(self, index, val):
    self.addMethods(f"__setitem__({index}, {json.dumps(val)})")

    return self
                       
  def getValue(self, index):
    return self.callMethod(f"__getitem__({index})")
                       
  def fill(self, val):
    self.addMethods(f"fill({json.dumps(val)})")
    return self

  def write(self):
    self.addMethods(f"write()")

class I2C_Core_(Core_):
  def __init__(self, sda = None, scl = None, *, device = None, soft = None):
    super().__init__(device)

    if sda == None != scl == None:
      raise Exception("None or both of sda/scl must be given!")
    elif sda != None:
      self.init(sda, scl, device = device, soft = soft)

  def scan(self):
    return (commit(f"{self.getObject()}.scan()"))


class I2C(I2C_Core_):
  def init(self, sda, scl, *, device = None, soft = False):
    if soft == None:
      soft = False

    super().init("I2C-1", f"machine.{'Soft' if soft else ''}I2C({'0,' if not soft else ''} sda=machine.Pin({sda}), scl=machine.Pin({scl}))", device = device)

class SoftI2C(I2C):
  def init(self, sda, scl, *, device = None, soft = True):
    if soft == None:
      soft = True

    super().init(sda, scl, device = device, soft = soft)
  
class HT16K33(Core_):
  def __init__(self, i2c = None, /, addr = None):
    super().__init__()

    if i2c:
      self.init(i2c)


  def init(self, i2c, addr = None):
    super().init("HT16K33-1", f"HT16K33({i2c.getObject()}, {addr})", i2c.getDevice())

    return self.addMethods(f"set_brightness(0)")


  def setBlinkRate(self, rate):
    return self.addMethods(f"set_blink_rate({rate})")


  def setBrightness(self, brightness):
    return self.addMethods(f"set_brightness({brightness})")

  def clear(self):
    return self.addMethods(f"clear()")

  def draw(self, motif):
    return self.addMethods(f"clear().draw('{motif}').render()")

  def plot(self, x, y, ink=True):
    return self.addMethods(f"plot({x}, {y}, ink={1 if ink else 0})")  

  def show(self):
    return self.addMethods(f"render()")


def getParam(label, value):
  if value:
    return f", {label} = {value}"
  else:
    return ""


class PWM(Core_):
  def __init__(self, pin = None, *, freq = None, ns = None, u16 = None, device = None):
    super().__init__(device)

    if pin != None:
      self.init(pin, device = device)


  def init(self, pin, *, freq = None, u16 = None, ns = None, device = None):
    super().init("PWM-1", f"machine.PWM(machine.Pin({pin}){getParam('freq', freq)}{getParam('duty_u16', u16)}{getParam('duty_ns', ns)})", device)


  def getU16(self):
    return int(self.callMethod("duty_u16()"))


  def setU16(self, u16):
    return self.addMethods(f"duty_u16({u16})")


  def getNS(self):
    return int(self.callMethod("duty_ns()"))


  def setNS(self, ns):
    return self.addMethods(f"duty_ns({ns})")


  def getFreq(self):
    return int(self.callMethod("freq()"))


  def setFreq(self, freq):
    return self.addMethods(f"freq({freq})")


  def deinit(self):
    return self.addMethods(f"deinit()")


class PCA9685(Core_):
  def __init__(self, i2c = None, *, addr = None):
    super().__init__()

    if i2c:
      self.init(i2c, addr = addr)

  def init(self, i2c, addr = None):
    super().init("PCA9685-1", f"PCA9685({i2c.getObject()}, {addr})", i2c.getDevice())

  def deinit(self):
    self.addMethods(f"reset()")

  def nsToU12_(self, duty_ns):
    return int(self.freq() * duty_ns * 0.000004095)
  
  def u12ToNS_(self, value):
    return int(200000000 * value / (self.freq() * 819))

  def getOffset(self):
    return int(self.callMethod("offset()"))

  def setOffset(self, offset):
    return self.addMethods(f"offset({offset})")

  def getFreq(self):
    return int(self.callMethod("freq()"))

  def setFreq(self, freq):
    return self.addMethods(f"freq({freq})")

  def getPrescale(self):
    return int(self.callMethod("prescale()"))

  def setPrescale(self, value):
    return self.addMethods(f"prescale({value})")
  

class PWM_PCA9685(Core_):
  def __init__(self, pca = None, channel = None):
    super().__init__()

    if bool(pca) != (channel != None):
      raise Exception("Both or none of 'pca' and 'channel' must be given!")
    
    if pca:
      self.init(pca, channel)

  def init(self, pca, channel):
    super().init("PWM_PCA9685-1", f"PWM_PCA9685({pca.getObject()}, {channel})", pca.getDevice())

    self.pca = pca # Not used inside this object, but to avoid pca being destroyed by GC, as it is used on the µc.

  def deinit(self):
    self.addMethods(f"deinit()")

  def getOffset(self):
    return self.pca.getOffset()

  def setOffset(self, offset):
    self.pca.setOffset(offset)

  def getNS(self):
    return int(self.callMethod(f"duty_ns()"))

  def setNS(self, ns):
    self.addMethods(f"duty_ns({ns})")

  def getU16(self, u16 = None):
    return int(self.callMethod("duty_u16()"))
  
  def setU16(self, u16):
    self.addMethods(f"duty_u16({u16})")
  
  def getFreq(self):
    return self.pca.getFreq()
  
  def setFreq(self, freq):
    self.pca.setFreq(freq)

  def getPrescale(self):
    return self.pca.getPrescale()
  
  def setPrescale(self, value):
    self.pca.setPrescale(value)
  

class LCD_PCF8574(Core_):
  def __init__(self, i2c, num_lines, num_columns,/,addr = None):
    super().__init__()

    if i2c:
      self.init(i2c, num_lines, num_columns, addr = addr)
    elif addr != None:
      raise Exception("addr can not be given without i2c!")

  def init(self, i2c, num_lines, num_columns, addr = None):
    return super().init("LCD_PCF8574-1", f"LCD_PCF8574({i2c.getObject()},{num_lines},{num_columns},{addr})", i2c.getDevice())

  def moveTo(self, x, y):
    return self.addMethods(f"move_to({x},{y})")

  def putString(self, string):
    return self.addMethods(f"putstr(\"{string}\")")

  def clear(self):
    return self.addMethods("clear()")

  def showCursor(self, value = True):
    return self.addMethods("show_cursor()" if value else "hide_cursor()")

  def hideCursor(self):
    return self.showCursor(False)

  def blinkCursorOn(self, value = True):
    return self.addMethods("blink_cursor_on()" if value else "blink_cursor_off()")

  def blinkCursorOff(self):
    return self.blinkCursorOn(False)

  def displayOn(self, value = True):
    return self.addMethods("display_on()" if value else "display_off()")

  def displayOff(self):
    return self.displayOn(False)

  def backlightOn(self, value = True):
    return self.addMethods("backlight_on()" if value else "backlight_off()")

  def backlightOff(self):
    return self.backlightOn(False)

  

class Servo(Core_):
  class Specs:
    def __init__(self, u16_min, u16_max, range):
      self.min = u16_min
      self.max = u16_max
      self.range = range
  
  class Tweak:
    def __init__(self, angle, u16_offset, invert):
      self.angle = angle
      self.offset = u16_offset
      self.invert = invert
  
  class Domain:
    def __init__(self, u16_min, u16_max):
      self.min = u16_min
      self.max = u16_max


  def test_(self, specs, tweak, domain):
    if tweak:
      if not specs:
        raise Exception("'tweak' can not be given without 'specs'!")

    if domain:
      if not specs:
        raise Exception("'domain' can not be given without 'specs'!")


  def __init__(self, pwm = None, specs = None, /, *, tweak = None, domain = None):
    super().__init__()

    self.test_(specs, tweak, domain)

    if pwm:
      self.init(pwm, specs, tweak = tweak, domain = domain)


  def init(self, pwm, specs, tweak = None, domain = None):
    super().init("Servo-1", "", pwm.getDevice())

    self.test_(specs, tweak, domain)

    if not tweak:
      tweak = self.Tweak(specs.range/2, 0, False)

    if not domain:
      domain = self.Domain(specs.min, specs.max)

    self.specs = specs
    self.tweak = tweak
    self.domain = domain

    self.pwm = pwm

    self.reset()


  def angleToDuty(self, angle):
    if self.tweak.invert:
      angle = -angle

    u16 = self.specs.min + ( angle + self.tweak.angle ) * ( self.specs.max - self.specs.min ) / self.specs.range + self.tweak.offset

    if u16 > self.domain.max:
      u16 = self.domain.max
    elif u16 < self.domain.min:
      u16 = self.domain.min

    return int(u16)
  

  def dutyToAngle(self, duty):
    angle = self.specs.range * ( duty - self.tweak.offset - self.specs.min ) / ( self.specs.mas - self.specs.min )

    if self.tweak.invert:
      angle = -angle

    return angle - self.tweak.angle


  def reset(self):
    self.setAngle(0)


  def getAngle(self):
    return self.dutyToAngle(self.pwm.getU16())

  def setAngle(self, angle):
    return self.pwm.setU16(self.angleToDuty(angle))
  

class SSD1306(Core_):
  def show(self):
    return self.addMethods("show()")

  def powerOff(self):
    return self.addMethods("poweroff()")

  def contrast(self, contrast):
    return self.addMethods(f"contrast({contrast})")

  def invert(self, invert):
    return self.addMethods(f"invert({invert})")

  def fill(self, col):
    return self.addMethods(f"fill({col})")

  def pixel(self, x, y, col = 1):
    return self.addMethods(f"pixel({x},{y},{col})")

  def scroll(self, dx, dy):
    return self.addMethods(f"scroll({dx},{dy})")

  def text(self, string, x, y, col=1):
    return self.addMethods(f"text('{string}',{x}, {y}, {col})")
  
  def rect(self, x, y, w, h, col, fill=True):
    return self.addMethods(f"rect({x},{y},{w},{h},{col},{fill})")

  def draw(self, pattern, width, ox = 0, oy = 0, mul = 1):
    if width % 4:
      raise Exception("'width' must be a multiple of 4!")
    return self.addMethods(f"draw('{pattern}',{width},{ox},{oy},{mul})")


class SSD1306_I2C(SSD1306):
  def __init__(self, width = None, height = None, i2c = None, /, addr = None, external_vcc = False):
    super().__init__()

    if bool(width) != bool(height) != bool(i2c):
      raise Exception("All or none of width/height/i2c must be given!")
    elif width:
      self.init(width, height, i2c, external_vcc = external_vcc, addr= addr)
    elif addr:
      raise Exception("addr can not be given without i2c!")
      
  def init(self, width, height, i2c, /, external_vcc = False, addr = None):
    super().init(("SSD1306-1", "SSD1306_I2C-1"), f"SSD1306_I2C({width}, {height}, {i2c.getObject()}, {addr}, {external_vcc})", i2c.getDevice())


def pwmJumps(jumps, step = 100, delay = 0.05, *,device = None):
  device = getDevice_(device)

  device.addModule("PWMJumps-1")

  command = "pwmJumps([\n"

  for jump in jumps:
    command += f"\t[{jump[0].getObject()},{jump[1]}],\n"

  command += f"], {step}, {delay})"

  device.addCommand(command)

def servoMoves(moves, step = 100, delay = 0.05, *,device = None):
  jumps = []
  
  for move in moves:
    servo = move[0]
    jumps.append([servo.pwm, servo.angleToDuty(move[1])])

  pwmJumps(jumps, step, delay, device = device)

def rbShade(variant, i, max):
  match int(variant) % 6:
    case 0:
      return [max, i, 0]
    case 1:
      return [max - i, max, 0]
    case 2:
      return [0, max, i]
    case 3:
      return [0, max - i, max]
    case 4:
      return [i, 0, max]
    case 5:
      return [max, 0, max - i]
      
def rbFade(variant, i, max, inOut):
  if not inOut:
    i = max - i
  match variant % 6:
    case 0:
      return [i,0,0]
    case 1:
      return [i,i,0]
    case 2:
      return [0,i,0]
    case 3:
      return [0,i,i]
    case 4:
      return [0,0,i]
    case 5:
      return [i,0,i]
      

def rbShadeFade(variant, i, max):
  if i < max:
    return rbFade(variant, i, max, True)
  elif i > max * 6:
    return rbFade((variant + 5 ) % 6, i % max, max, False)
  else:
    return rbShade(variant + int( (i - max) / max ), i % max, max)
    
