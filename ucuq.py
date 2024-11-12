###########################
#      DO NOT MODIFY      #
# COMPUTER GENERATED FILE #
###########################

import os, json, socket, sys, threading, datetime, time
from inspect import getframeinfo, stack

CONFIG_FILE = ( "/home/csimon/q37/epeios/tools/ucuq/remote/wrappers/PYH/" if "Q37_EPEIOS" in os.environ else "../" ) + "ucuq.json"

if not os.path.isfile(CONFIG_FILE):
  print("Please launch the 'Config' app first to set the device to use!")
  sys.exit(0)

with open(CONFIG_FILE, "r") as config:
  CONFIG_ = json.load(config)

UCUQ_DEFAULT_HOST_ = "ucuq.q37.info"
UCUQ_DEFAULT_PORT_ = "53800"

UCUQ_HOST_ = CONFIG_["Proxy"]["Host"] if "Proxy" in CONFIG_ and "Host" in CONFIG_["Proxy"] and CONFIG_["Proxy"]["Host"] else UCUQ_DEFAULT_HOST_

# only way to test if the entry contains a valid int.
try:
  UCUQ_PORT_ = int(CONFIG_["Proxy"]["Port"])
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


def ignition_(socket, token, deviceId):
  writeString_(socket, token)
  writeString_(socket, deviceId)

  error = readString_(socket)

  if error:
    raise Error(error)


def connect_(token, deviceId):
  socket = init_()
  handshake_(socket)
  ignition_(socket, token, deviceId)

  return socket


class Error(Exception):
  pass

def commit(expression=""):
  return getDevice_().commit(expression)

def sleep(secs):
  return getDevice_().sleep(secs)

def getTokenAndDeviceId():
  return getDevice_().getTokenAndDeviceId()

def getToken():
  return getDevice_().getToken()

def getDeviceId():
  return getDevice_().getDeviceId()

CONFIG_DEVICE_ENTRY = "Device"
CONFIG_DEVICE_TOKEN_ENTRY = "Token"
CONFIG_DEVICE_ID_ENTRY = "Id"

def displayMissingConfigMessage_():
  raise Error("Please launch the 'Config' app first to set the device to use!")

def handlingConfig_(token, id):
  if CONFIG_DEVICE_ENTRY not in CONFIG_:
    displayMissingConfigMessage_()

  device = CONFIG_[CONFIG_DEVICE_ENTRY]

  if token == None:
    if CONFIG_DEVICE_TOKEN_ENTRY not in device:
      displayMissingConfigMessage_()

    token = device[CONFIG_DEVICE_TOKEN_ENTRY]

  if id == None:
    if CONFIG_DEVICE_ID_ENTRY not in device:
      displayMissingConfigMessage_()

    id = device[CONFIG_DEVICE_ID_ENTRY]

  return token, id


class Device_:
  def __init__(self, /, id = None, token = None, now = True):
    self.socket_ = None

    if now:
      self.connect(id, token)

  def connect(self, id, token):
    if token == None or id == None:
      token, id = handlingConfig_(token, id)

    self.token = token
    self.id = id

    self.socket_ = connect_(self.token, self.id)

  def getTokenAndDeviceId(self):
    return self.token, self.id

  def getToken(self):
    return self.getTokenAndDeviceId()[0]

  def getDeviceId(self):
    return self.getTokenAndDeviceId()[1]

  def upload(self, modules):
    writeString_(self.socket_, R_UPLOAD_)
    writeStrings_(self.socket_, modules)

    if ( answer := readUInt_(self.socket_) ) == A_OK_:
      pass
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
  def __init__(self, /, id = None, token = None, now = True):
    self.pendingModules = ["Init_1"]
    self.handledModules = []
    self.commands = []

    super().__init__(id, token, now)

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

###############
# UCUq COMMON #
###############

INFO_SCRIPT = """
def ucuqGetKitLabel(): 
  if "Kit" in CONFIG_:
    kit = CONFIG_["Kit"]

    id = getSelectorId_(SELECTOR_)

    if id in kit:
      return kit[id]
    else:
      return ""

def ucuqStructToDict(obj):
    return {attr: getattr(obj, attr) for attr in dir(obj) if not attr.startswith('__')}

def ucuqGetInfos():
  return {
    "kit": {
      "label": ucuqGetKitLabel()
    },
    "uname": ucuqStructToDict(uos.uname())
  }
"""

def handleATK(dom):
  dom.inner("", "<h3>Connecting…</h3>")
  
  addCommand(INFO_SCRIPT)

  try:
    info = commit("ucuqGetInfos()")
  except Exception as err:
    dom.inner("", f"<h5>Error: {err}</h5>")
    raise

  dom.inner("", f"<h3>'{info['kit']['label']}'</h3>")

  time.sleep(1.5)

  return info

def getDevice_(device = None):
  if device == None:
    global device_

    if device_ == None:
      device_ = Device()
    
    return device_
  else:
    return device

def addCommand(command, /,device = None):
  getDevice_(device).addCommand(command)

def servoMoves(moves, speed = 1,/,device = None):
  device = getDevice_(device)

  device.addModule("ServoMoves-1")

  command = "servoMoves([\n"

  for move in moves:
    servo = move[0]

    step = speed * (servo.specs.max - servo.specs.min) / servo.specs.range

    command += f"\t[{move[0].pwm.getObject()},{move[0].angleToDuty(move[1])}],\n"

  command += f"], {int(step)})"

  device.addCommand(command)


class Core_:
  def __init__(self, device, modules = ""):
    self.id = None

    self.device_ = getDevice_(device)

    if modules:
      self.device_.addModules(modules)
  
  def __del__(self):
    if self.id:
      self.addCommand(f"del {ITEMS_}[{self.id}]")
  
  def init(self, instanciation):
    self.id = GetUUID_()
    if instanciation:
      self.addCommand(f"{self.getObject()} = {instanciation}")

  def getObject(self):
    return f"{ITEMS_}[{self.id}]"

  def addCommand(self, command):
    self.device_.addCommand(command)

  def addMethods(self, methods):
    self.addCommand(f"{self.getObject()}.{methods}")
                         

class GPIO(Core_):
  def __init__(self, pin = None, device = None):
    super().__init__(device, "GPIO-1")

    if pin:
      self.init(pin)


  def init(self, pin):
    self.pin = f'"{pin}"' if isinstance(pin,str) else pin

    super().init(f"GPIO({self.pin})")


  def high(self, value = True):
    self.addMethods(f"high({value})")


  def low(self):
    self.high(False)


class WS2812(Core_):
  def __init__(self, pin = None, n = None, device = None):
    super().__init__(device, "WS2812-1")

    if (pin == None) != (n == None):
      raise Exception("Both or none of 'pin'/'n' must be given")

    if pin != None:
      self.init(pin, n)

  def init(self, pin, n):
    super().init(f"neopixel.NeoPixel(machine.Pin({pin}), {n})")

  def len(self):
    return int(self.execute_("", f"{self.getObject()}.__len__()"))
               

  def setValue(self, index, val):
    self.addMethods(f"setitem({index}, {json.dumps(val)})")

    return self
                       
  def getValue(self, index):
    return self.execute_("", f"{self.getObject()}.__getitem__({index})")
                       
  def fill(self, val):
    self.addMethods(f"fill({json.dumps(val)})")
    return self

  def write(self):
    self.addMethods(f"write()")

class I2C(Core_):
  def __init__(self, sda = None, scl = None, /, device = None):
    super().__init__(device, "I2C-1")

    if bool(sda) != bool(scl):
      raise Exception("None or both of sda/scl must be given!")
    elif sda != None:
      self.init(sda, scl)

  def init(self, sda, scl):
    super().init(f"machine.I2C(0, sda=machine.Pin({sda}), scl=machine.Pin({scl}))")

  def scan(self):
    return (commit(f"{self.getObject()}.scan()"))
    

class HT16K33(Core_):
  def __init__(self, i2c = None, /, addr = None, device = None):
    super().__init__(device, "HT16K33-1")

    if i2c:
      self.init(i2c)


  def init(self, i2c, addr = None):
    super().init(f"HT16K33({i2c.getObject()}, {addr})")

    self.addMethods(f"set_brightness(0)")


  def setBlinkRate(self, rate):
    self.addMethods(f"set_blink_rate({rate})")

    return self

  def setBrightness(self, brightness):
    self.addMethods(f"set_brightness({brightness})")

    return self

  def clear(self):
    self.addMethods(f"clear()")

    return self

  def draw(self, motif):
    self.addMethods(f"clear().draw('{motif}').render()")

    return self

  def plot(self, x, y, ink=True):
    self.addMethods(f"plot({x}, {y}, ink={1 if ink else 0})")  

    return self

  def show(self):
    self.addMethods(f"render()")

    return self


class PWM(Core_):
  def __init__(self, pin = None, freq = None, device = None):
    super().__init__(device, "PWM-1")

    if freq != None:
      if pin == None:
        raise Exception("'freq' cannot be given without 'pin'!")
      
    if pin != None:
      self.init(pin, freq)


  def init(self, pin, freq = None):
    super().init(f"machine.PWM(machine.Pin({pin}),freq={freq if freq else 50})")


  def getU16(self):
    return int(self.execute_("", f"{self.getObject()}.duty_u16()"))


  def setU16(self, u16):
    self.addMethods(f"duty_u16({u16})")


  def getNS(self):
    return int(self.execute_("", f"{self.getObject()}.duty_ns()"))


  def setNS(self, ns):
    self.addMethods(f"duty_ns({ns})")


  def getFreq(self):
    return int(self.execute_("", f"{self.getObject()}.freq()"))


  def setFreq(self, freq):
    self.addMethods(f"freq({freq})")


  def deinit(self):
    self.addMethods(f"deinit()")


class PCA9685(Core_):
  def __init__(self, i2c = None, freq = None,/, addr = None, device = None):
    super().__init__(device, "PCA9685-1")

    if i2c:
      self.init(i2c, freq = freq, addr = addr)
    elif freq:
      raise Exception("freq cannot be given without i2c!")
    elif addr:
      raise Exception("addr cannot be given without i2c!")


  def init(self, i2c, /, freq = None, addr = None):
    super().init(f"PCA9685({i2c.getObject()}, {addr})")

    self.setFreq(freq if freq else 50)


  def deinit(self):
    self.addMethods(f"reset()")
                    

  def nsToU12_(self, duty_ns):
    return int(self.freq() * duty_ns * 0.000004095)
  
  def u12ToNS_(self, value):
    return int(200000000 * value / (self.freq() * 819))

  def getFreq(self):
    return self.execute_("", f"{self.getObject()}.freq()")

  def setFreq(self, freq):
    return self.addMethods(f"freq({freq})")
  

class PWM_PCA9685(Core_):
  def __init__(self, pca = None, channel = None, device = None):
    super().__init__(device, "PWM_PCA9685-1")

    if bool(pca) != (channel != None):
      raise Exception("Both or none of 'pca' and 'channel' must be given!")
    
    if pca:
      self.init(pca, channel)


  def init(self, pca, channel):
    super().init(f"PWM_PCA9685({pca.getObject()}, {channel})")

    self.pca = pca # Not used inside this object, but to avoid pca being destroyed by GC, as it is used on the µc.

  def deinit(self):
    self.addMethods(f"deinit()")


  def getNS(self,):
    return int(self.execute_("", f"{self.getObject()}.duty_ns()"))

  def setNS(self, ns):
    self.addMethods(f"duty_ns({ns})")


  def getU16(self, u16 = None):
    return int(self.execute_("",f"{self.getObject()}.duty_u16()"))
  
  def setU16(self, u16):
    self.addMethods(f"duty_u16({u16})")
  

  def getFreq(self):
    return int(self.execute_("",f"{self.getObject()}.freq()"))
  
  def setFreq(self, freq):
    self.addMethods(f"freq({freq})")


class LCD_PCF8574(Core_):
  def __init__(self, i2c, num_lines, num_columns,/,addr = None, device = None):
    super().__init__(device, "LCD_PCF8574-1")

    if i2c:
      self.init(i2c, num_lines, num_columns, addr = addr)
    elif addr != None:
      raise Exception("addr can not be given without i2c!")

  def init(self, i2c, num_lines, num_columns, addr = None):
    super().init(f"LCD_PCF8574({i2c.getObject()},{num_lines},{num_columns},{addr})")

  def moveTo(self, x, y):
    self.addMethods(f"move_to({x},{y})")

  def putString(self, string):
    self.addMethods(f"putstr(\"{string}\")")

  def clear(self):
    self.addMethods("clear()")

  def showCursor(self, value = True):
    self.addMethods("show_cursor()" if value else "hide_cursor()")

  def hideCursor(self):
    self.showCursor(False)

  def blinkCursorOn(self, value = True):
    self.addMethods("blink_cursor_on()" if value else "blink_cursor_off()")

  def blinkCursorOff(self):
    self.blinkCursorOn(False)

  def displayOn(self, value = True):
    self.addMethods("display_on()" if value else "display_off()")

  def displayOff(self):
    self.displayOn(False)

  def backlightOn(self, value = True):
    self.addMethods("backlight_on()" if value else "backlight_off()")

  def backlightOff(self):
    self.backlightOn(False)

  

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


  def __init__(self, pwm = None, specs = None, /, *, tweak = None, domain = None, device = None):
    super().__init__(device, "Servo-1")

    self.test_(specs, tweak, domain)

    if pwm:
      self.init(pwm, specs, tweak = tweak, domain = domain)


  def init(self, pwm, specs, tweak = None, domain = None):
    super().init("")

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
    self.addMethods("show()")

  def powerOff(self):
    self.addMethods("poweroff()")

  def contrast(self, contrast):
    self.addMethods(f"contrast({contrast})")

  def invert(self, invert):
    self.addMethods(f"invert({invert})")

  def fill(self, col):
    self.addMethods(f"invert({col})")

  def pixel(self, x, y, col):
    self.addMethods(f"pixel({x},{y},{col})")

  def scroll(self, dx, dy, col):
    self.addMethods(f"scroll({dx},{dy})")

  def text(self, string, x, y, col=1):
    self.addMethods(f"text('{string}',{x}, {y}, {col})")

class SSD1306_I2C(SSD1306):
  def __init__(self, width = None, height = None, i2c = None, /, addr = None, external_vcc = False, device = None):
    super().__init__(device, ("SSD1306-1", "SSD1306_I2C-1"))

    if bool(width) != bool(height) != bool(i2c):
      raise Exception("All or none of width/height/i2c must be given!")
    elif width:
      self.init(width, height, i2c, external_vcc = external_vcc, addr= addr)
    elif addr:
      raise Exception("addr can not be given without i2c!")
      

  def init(self, width, height, i2c, /, external_vcc = False, addr = None):
    super().init(f"SSD1306_I2C({width}, {height}, {i2c.getObject()}, {addr}, {external_vcc})")



    
