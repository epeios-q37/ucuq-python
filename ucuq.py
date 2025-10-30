###########################
#      DO NOT MODIFY      #
# COMPUTER GENERATED FILE #
###########################

import datetime, http, os, json, socket, ssl, sys, threading, urllib
from inspect import getframeinfo, stack


CONFIG_FILE_ = ( "/home/csimon/q37/epeios/other/BPY/Apps/UCUq/" if "Q37_EPEIOS" in os.environ else "../" ) + "ucuq.json"
KITS_FILE_ = ( "/home/csimon/epeios/other/BPY/Apps/UCUq/assets/" if "Q37_EPEIOS" in os.environ else "../assets/" ) + "kits.json"

try:
  with open(CONFIG_FILE_, "r") as config:
    CONFIG_ = json.load(config)
except:
  CONFIG_ = None


try:
  with open(KITS_FILE_, "r") as kits:
    KITS_ = json.load(kits)
except:
  KITS_ = None


UCUQ_DEFAULT_HOST_ = "ucuq.q37.info"
UCUQ_DEFAULT_PORT_ = "53843"
UCUQ_DEFAULT_SSL_ = True

UCUQ_HOST_ = CONFIG_["Proxy"]["Host"] if CONFIG_ and "Proxy" in CONFIG_ and "Host" in CONFIG_["Proxy"] and CONFIG_["Proxy"]["Host"] else UCUQ_DEFAULT_HOST_

# only way to test if the entry contains a valid int.
try:
  UCUQ_PORT_ = int(CONFIG_["Proxy"]["Port"])
except:
  UCUQ_PORT_ = int(UCUQ_DEFAULT_PORT_)

UCUQ_SSL_ = CONFIG_["Proxy"]["SSL"] if CONFIG_ and "Proxy" in CONFIG_ and "SSL" in CONFIG_["Proxy"] and CONFIG_["Proxy"]["SSL"] != None else UCUQ_DEFAULT_SSL_


PROTOCOL_LABEL_ = "c37cc83e-079f-448a-9541-5c63ce00d960"
PROTOCOL_VERSION_ = "0"

writeLock_ = threading.Lock()

Lock_ = threading.Lock

# Request
R_EXECUTE_ = "Execute_1"
R_UPLOAD_ = "Upload_1"

# Answer
# Answer; must match in device.h: device::eAnswer.
A_RESULT_ = 0
A_SENSOR_ = 1
A_ERROR_ = 2
A_PUZZLED_ = 3
A_DISCONNECTED_ = 4

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
  print("Connection to UCUq server…", end="", flush=True)

  try:
    s = socket.create_connection((UCUQ_HOST_, UCUQ_PORT_))
    if UCUQ_SSL_:
      s = ssl.create_default_context().wrap_socket(s, server_hostname="q37.info" if UCUQ_HOST_ == UCUQ_DEFAULT_HOST_ else UCUQ_HOST_)
  except Exception as e:
    raise e
  else:
    print("\r                                         \r",end="")

  return s


def handshake_(socket):
  with writeLock_:
    writeString_(socket, PROTOCOL_LABEL_)
    writeString_(socket, PROTOCOL_VERSION_)
    writeString_(socket, "Remote")
    writeString_(socket, "PYH")

  error = readString_(socket)

  if error:
    exit_(error)

  notification = readString_(socket)

  if notification:
    pass
    # print(notification)


def ignition_(socket, token, deviceId, errorAsException):
  with writeLock_:
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
  return getDevice().commit(expression)


def displayExitMessage_(Message):
  raise Error(Message)


def readingThread(proxy):
  while True:
    if ( answer := readUInt_(proxy.socket) ) == A_RESULT_:
      proxy.resultBegin.set()
      proxy.resultEnd.wait()
      proxy.resultEnd.clear()
    elif answer == A_SENSOR_:
      raise Error("Sensor handling not yet implemented!")
    elif answer == A_ERROR_:
      result = readString_(proxy.socket)
      print(f"\n>>>>>>>>>> ERROR FROM DEVICE BEGIN <<<<<<<<<<")
      print("Timestamp: ", datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') )
      caller = getframeinfo(stack()[1][0])
      print(f"Caller: {caller.filename}:{caller.lineno}")
      print(f">>>>>>>>>> ERROR FROM DEVICE CONTENT <<<<<<<<<<")
      print(result)
      print(f">>>>>>>>>> END ERROR FROM DEVICE END <<<<<<<<<<")
      proxy.exit = True
      proxy.resultBegin.set()
      exit_()
    elif answer == A_PUZZLED_:
      readString_(proxy.socket) # For future use
      raise Error("Puzzled!")
    elif answer == A_DISCONNECTED_:
        raise Error("Disconnected from device!")
    else:
      raise Error("Unknown answer from device!")


class Proxy:
  def __init__(self, socket):
    self.socket = socket
    if socket != None:
      self.resultBegin = threading.Event()
      self.resultEnd = threading.Event()
      self.exit = False
      threading.Thread(target = readingThread, args=(self,)).start()


class Device_:
  def __init__(self, *, id = None, token = None, callback = None):
    if callback != None:
      exit_("'callback' in only used by the Brython version!")

    if id or token:
      self.connect(id, token)

  def connect(self, id = None, token = None, errorAsException = True):
    if token == None and id == None:
      token, id = handlingConfig_(token, id)

    if not token:
      token = getConfigToken_()

    self.token = token if token else DEMO_VTOKEN
    self.id = id if id else ""

    self.proxy = Proxy(connect_(self.token, self.id, errorAsException = errorAsException))

    return self.proxy.socket != None
  
  def upload_(self, modules):
    with writeLock_:
      writeString_(self.proxy.socket, R_UPLOAD_)
      writeStrings_(self.proxy.socket, modules)

  def execute_(self, script, expression = ""):
    if self.proxy.socket:
      with writeLock_:
        writeString_(self.proxy.socket, R_EXECUTE_)
        writeString_(self.proxy.socket, script)
        writeString_(self.proxy.socket, expression)

      if expression:
        self.proxy.resultBegin.wait()
        self.proxy.resultBegin.clear()
        if self.proxy.exit:
          exit()
        else:
          result = readString_(self.proxy.socket)
          self.proxy.resultEnd.set()

          if result:
            return json.loads(result)
          else:
            return None
          
  def commit(self, expression = ""):
    result = ""

    if self.pendingModules_:
      self.upload_(self.pendingModules_)
      self.handledModules_.extend(self.pendingModules_)
      self.pendingModules_ = []

    if self.commands_ or expression:
      result = self.execute_('\n'.join(self.commands_), expression)
      self.commands_ = []

    return result

def getWebFileContent(url):
  parsedURL = urllib.parse.urlparse(url)

  with http.client.HTTPSConnection(parsedURL.netloc) as connection:
    connection.request("GET", parsedURL.path)

    response = connection.getresponse()

    if response.status == 200:
      return response.read().decode('utf-8')  
    else:
      raise Exception(f"Error retrieving the file '{url}': {response.status} {response.reason}")
    
def getKits():
  pass# With Python, the kits are already retrieved.

###############
# COMMON PART #
###############


import zlib, base64, time, atlastk, binascii

ITEMS_ = "i_"

# Keys
K_DEVICE = "Device"
K_DEVICE_TOKEN = "Token"
K_DEVICE_ID = "Id"

DEMO_VTOKEN = "84210c27-cdf8-438f-8641-a2e12380c2cf"

FLASH_DELAY_ = 0

objectCounter_ = 0
device_ = None

unpack_ = lambda data: zlib.decompress(base64.b64decode(data)).decode()


def getObjectIndice():
  global objectCounter_

  objectCounter_ += 1

  return objectCounter_


def getObject_(id):
  return f"{ITEMS_}[{id}]"


def displayMissingConfigMessage_():
  displayExitMessage_(
    "Please launch the 'Config' app first to set the device to use!"
  )


def handlingConfig_(token, id):
  if not CONFIG_:
    displayMissingConfigMessage_()

  if K_DEVICE not in CONFIG_:
    displayMissingConfigMessage_()

  device = CONFIG_[K_DEVICE]

  if not token:
    if K_DEVICE_TOKEN not in device:
      displayMissingConfigMessage_()

    token = device[K_DEVICE_TOKEN]

  if not id:
    if K_DEVICE_ID not in device:
      displayMissingConfigMessage_()

    id = device[K_DEVICE_ID]

  return token, id


def getConfigToken_():
  try:
    return CONFIG_[K_DEVICE][K_DEVICE_TOKEN]
  except:
    return ""


def setDevice(id=None, *, device=None, token=None):
  if device != None:
    global device_
    if id or token:
      raise Exception("'device' can not be given together with 'id' or 'token'!")
    device_ = device
  else:
    getDevice(id=id, token=token)


# Infos keys and subkeys
IK_DEVICE_ID_ = "DeviceId"
IK_DEVICE_UNAME_ = "uname"
IK_HARDWARE = "Hardware"
IK_FEATURES = "Features"
IK_KIT_LABEL = "KitLabel"

# Kits keys
IK_BRAND_ = "brand"
IK_MODEL_ = "model"
IK_VARIANT_ = "variant"


INFO_SCRIPT_ = f"""
def ucuqStructToDict(obj):
  return {{attr: getattr(obj, attr) for attr in dir(obj) if not attr.startswith('__')}}

def ucuqGetInfos():
  infos = {{
  "{IK_DEVICE_ID_}": ucuq.settings.getDeviceId(),
  "{IK_DEVICE_UNAME_}": ucuqStructToDict(__import__('uos').uname())
  }}

  if kit := ucuq.settings.getKitLabel():
    infos["{IK_KIT_LABEL}"] = kit

  return infos
"""

ATK_BODY_ = (
  """
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
<div style="display: flex; justify-content: center;" class="ucuq">
  <h3>'BRACES' (<em>BRACES</em>)</h3>
</div>
<div id="ucuq_body" style_="display: flex; justify-content: center;">
</div>
""".replace(
    "{", "{{"
  )
  .replace("}", "}}")
  .replace("BRACES", "{}")
)


ATK_XDEVICE_ = """
<dialog id="ucuq_xdevice" style="width: min-content;">
  <fieldset>
    <legend>Device</legend>
    <label style="display: flex; justify-content: space-between; margin: 5px;">
      <span>Token:&nbsp;</span>
      <input id="ucuq_xdevice_token">
    </label>
    <label style="display: flex; justify-content: space-between; margin: 5px;">
      <span>Id:&nbsp;</span>
      <input id="ucuq_xdevice_id">
    </label>
  </fieldset>
  <div style="display: flex; justify-content: space-around; margin: 5px;">
    <button xdh:onevent="ucuq_xdevice_ok"/>{}</button>
    <button xdh:onevent="ucuq_xdevice_cancel">{}</button>
  </div>
  <fieldset>{}</fieldset>
</dialog>
"""

UCUQ_XDEVICE_ACTION_ = "UCUqXDevice"


def handleXDevice_(dom, response):
  dom.executeVoid("document.getElementById('ucuq_xdevice').close();")

  if response:
    atlastk.getUserGlobals()["UCUqXDevice"](
      dom,
      Device(
        id=dom.getValue("ucuq_xdevice_id"),
        token=dom.getValue("ucuq_xdevice_token"),
      ),
    )

  dom.executeVoid("element = document.getElementById('ucuq_xdevice').remove();")


def getDOM_(dom1, dom2):
  if isinstance(dom1, atlastk.DOM):
    return dom1
  else:
    return dom2


UCUQ_XDEVICE_I10N = (
  ("OK", "Cancel", "Click on ‘Cancel’ unless you know exactly what you're doing!"),
  (
    "OK",
    "Annuler",
    "Cliquez sur 'Annuler' à moins que vous ne sachiez exactement ce que vous faites !",
  ),
)


def handleXDeviceRetrieving_(dom1, dom2):
  dom = getDOM_(dom1, dom2)

  language = dom.language

  i10n = UCUQ_XDEVICE_I10N[
    1 if (language[:2].upper() if len(language) >= 2 else "") == "FR" else 0
  ]

  dom.end("", ATK_XDEVICE_.format(*i10n))

  atlastk.setCallback("ucuq_xdevice_ok", handleXDeviceOK_)
  atlastk.setCallback("ucuq_xdevice_cancel", handleXDeviceCancel_)

  dom.executeVoid(f"document.getElementById('ucuq_xdevice').showModal();")


def handleXDeviceOK_(dom1, dom2):
  handleXDevice_(getDOM_(dom1, dom2), True)


def handleXDeviceCancel_(dom1, dom2):
  handleXDevice_(getDOM_(dom1, dom2), False)


CB_AUTO = 0
CB_MANUAL = 1

defaultCommitBehavior_ = CB_AUTO


def testCommit_(commit, behavior=None):
  if commit == None:
    if behavior == None:
      behavior = defaultCommitBehavior_

    return behavior == CB_AUTO
  else:
    return commit


def sleepStart(id=None):
  return getDevice().sleepStart(id)


def sleepWait(id, secs):
  return getDevice().sleepWait(id, secs)


def sleep(secs):
  return getDevice().sleep(secs)


patchKeys_ = lambda keys: keys if keys else []

B_LCD = "LCD"
B_OLED = "OLED"
B_BUZZER = "Buzzer"
B_LOUDSPEAKER = "Loudspeaker"
B_SMART_RGB = "SmartRGB"
B_MATRIX = "Matrix"
B_TFT = "TFT"


class Auto:
  def __new__(cls, bit, infos, item, hardwareKeys, featuresKeys, **kwargs):
    hardware = getKitHardware_(infos)
    features = getKitFeatures_(infos)

    if not hasHardware_(hardware, item) and not hasFeatures_(features, item):
      return Nothing()

    hardwareKeys = patchKeys_(hardwareKeys)
    featuresKeys = patchKeys_(featuresKeys)

    return bit(
      *getDescItems_(features, item, featuresKeys),
      *getDescItems_(hardware, item, hardwareKeys),
      **kwargs,
    )


def getBits(infos, *bitLabels, device=None):
  bits = [getDevice(device)]

  for label in bitLabels:
    match label:
      case "LCD":
        bits.append(
          Auto(
            HD44780_I2C,
            infos,
            label,
            None,
            ["Width", "Height"],
            i2c=Auto(
              I2C,
              infos,
              label,
              ["SDA", "SCL", "Soft"],
              None,
              device=device,
            ),
          )
        )
      case "OLED":
        bits.append(
          Auto(
            OLED_I2C,
            infos,
            label,
            None,
            ["Driver", "Width", "Height"],
            i2c=Auto(
              I2C,
              infos,
              label,
              ["SDA", "SCL", "Soft"],
              None,
              device=device,
            ),
          )
        )
      case "Buzzer" | "Loudspeaker":
        bits.append(Auto(PWM, infos, label, ["Pin"], None, device=device))
      case "SmartRGB":
        bits.append(
          Auto(WS2812, infos, label, ["Pin"], ["Count"], device=device)
        )
      case "Matrix":
        bits.append(
          Auto(
            HT16K33,
            infos,
            label,
            None,
            None,
            i2c=Auto(
              I2C,
              infos,
              "Matrix",
              ["SDA", "SCL", "Soft"],
              None,
              device=device,
            ),
          )
        )
      case "TFT":
        bits.append(
          Auto(
            ILI9341,
            infos,
            label,
            ["DC", "CS", "RST"],
            ["Width", "Height", "Rotation"],
            spi=Auto(
              SPI,
              infos,
              label,
              ["Id", "SCK", "MOSI", "MISO", "Baudrate"],
              None,
              device=device,
            ),
          )
        )
      case _:
        raise Exception(f"Unknown bit label: {label}")

  return bits


class Multi:
  def __init__(self, object):
    self.objects = [object]

  def add(self, object):
    self.objects.append(object)

  def __getattr__(self, methodName):
    def wrapper(*args, **kwargs):
      for obj in self.objects:
        getattr(obj, methodName)(*args, **kwargs)
      return self

    return wrapper

  def __getitem__(self, index):
    if index < len(self.objects):
      return self.objects[index]
    else:
      raise IndexError("Index out of range for Multi object.")

  # Workaround for Brython (https://github.com/brython-dev/brython/issues/2590)
  def __bool__(self):
    return True


class Device(Device_):
  def __init__(self, *, id=None, token=None, callback=None):
    self.pendingModules_ = ["Init-1"]
    self.handledModules_ = []
    self.commands_ = [
"""
def sleepWait(start, us):
  elapsed = time.ticks_us() - start
            
  if elapsed < us:
    time.sleep_us(int(us - elapsed))
"""
    ]
    self.commitBehavior = None

    super().__init__(id=id, token=token, callback=callback)

  def __del__(self):
    self.commit()

  def testCommit_(self, commit):
    return testCommit_(commit, self.commitBehavior)

  def addModule(self, module):
    if not module in self.pendingModules_ and not module in self.handledModules_:
      self.pendingModules_.append(module)

    return self

  def addModules(self, modules):
    if isinstance(modules, str):
      self.addModule(modules)
    else:
      for module in modules:
        self.addModule(module)

    return self

  def addCommand(self, command, commit=None):
    self.commands_.append(command)

    if self.testCommit_(commit):
      self.commit()

    return self

  def sleepStart(self, id=None):
    if id == None:
      id = getObjectIndice()

    self.addCommand(f"{getObject_(id)} = time.ticks_us()")

    return id

  def sleepWait(self, id, secs):
    self.addCommand(f"sleepWait({getObject_(id)}, {secs * 1000000})")

  def sleep(self, secs):
    self.addCommand(f"time.sleep_us({int(secs * 1000000)})")


def getBaseInfos_(device=None):
  device = getDevice(device)

  device.addCommand(INFO_SCRIPT_, False)

  return device.commit("ucuqGetInfos()")


def getKitFromDeviceId_(deviceId):
  for kit in KITS_:
    if "devices" in kit and deviceId in kit["devices"]:
      return kit
  else:
    return None


buildKitLabel_ = lambda brand, model, variant: f"{brand}/{model}/{variant}"


def getKitLabelFromDeviceId_(deviceId):
  kit = getKitFromDeviceId_(deviceId)

  if kit:
    return buildKitLabel_(kit[IK_BRAND_], kit[IK_MODEL_], kit[IK_VARIANT_])
  else:
    return "Undefined"


def getKitFromLabel_(label):
  brand, model, variant = label.split("/")

  for kit in KITS_:
    if (
      kit["brand"] == brand
      and kit["model"] == model
      and kit["variant"] == variant
    ):
      return kit
  else:
    return None


def getKitLabel(infos):
  return infos[IK_KIT_LABEL]


def getKit_(infosOrLabel):
  if type(infosOrLabel) != str:
    infosOrLabel = getKitLabel(infosOrLabel)

  return getKitFromLabel_(infosOrLabel)


def getKitDesc_(infosOrLabel, descLabel):
  kit = getKit_(infosOrLabel)

  if kit:
    return kit[descLabel]
  else:
    return "Undefined"


def getKitHardware_(infosOrLabel):
  return getKitDesc_(infosOrLabel, "hardware")


def getKitFeatures_(infosOrLabel):
  return getKitDesc_(infosOrLabel, "features")


subGetDescItems_ = lambda desc, key, index: (
  desc[key][index] if key in desc and index < len(desc[key]) else None
)


def getDescItems_(kitDesc, stringOrList, keys=None, *, index=0):
  if type(stringOrList) == str:
    items = subGetDescItems_(kitDesc, stringOrList, index)
  else:
    for key in stringOrList:
      if items := subGetDescItems_(kitDesc, key, index):
        break

  if items and (keys or keys == []):
    result = tuple(
      items[keys] if type(keys) == str else (items[key] for key in keys)
    )
  elif items:
    result = items
  else:
    result = ()

  return result


def hasHardware_(kitHardware, item):
  return bool(getDescItems_(kitHardware, item))


def hasFeatures_(kitFeatures, item):
  return bool(getDescItems_(kitFeatures, item))


def getFeatures(infosOrLabel, item, keys=None, *, index=0):
  kitFeatures = getKitFeatures_(infosOrLabel)

  if not kitFeatures:
    return ()

  return getDescItems_(kitFeatures, item, keys, index=index)


def getHardware(infosOrLabel, item, keys=None, *, index=0):
  kitHardware = getKitHardware_(infosOrLabel)

  if not kitHardware:
    return ()

  return getDescItems_(kitHardware, item, keys, index=index)


def getDeviceId(infos):
  return infos[IK_DEVICE_ID_]


def getInfos(device):
  infos = getBaseInfos_(device)

  if not IK_KIT_LABEL in infos:
    infos[IK_KIT_LABEL] = getKitLabelFromDeviceId_(getDeviceId(infos))
  infos[IK_HARDWARE] = getKitDesc_(infos, "hardware")
  infos[IK_FEATURES] = getKitDesc_(infos, "features")

  return infos


def ATKConnect(dom, body, *, target="", device=None):
  getKits()

  if not KITS_:
    raise Exception("No kits defined!")

  dom.inner(
    target,
    """
  <style>
  .ucuq-connection {
    display: inline-block;
    /* Pour éviter les retours à la ligne */
    white-space: nowrap;
    /* Pour que le texte ne déborde pas */
    overflow: hidden;
    /* Animation en continu */
    animation: ucuq-connection 1s linear infinite;
    /* Masque linéaire horizontal */
    -webkit-mask-image: linear-gradient(to right, transparent 0%, black 50%, transparent 100%);
    mask-image: linear-gradient(to right, transparent 0%, black 50%, transparent 100%);
    -webkit-mask-size: 200% 100%;
    mask-size: 200% 100%;
    -webkit-mask-position: 0% 0%;
    mask-position: 0% 0%;
  }

  @keyframes ucuq-connection {
    100% {
    -webkit-mask-position: 0% 0%;
    mask-position: 0% 0%;
    }
    50% {
    -webkit-mask-position: 100% 0%;
    mask-position: 100% 0%;
    }
    0% {
    -webkit-mask-position: 200% 0%;
    mask-position: 200% 0%;
    }
  }
  </style>
  <h2 class="ucuq-connection">💻…📡…🛰️…<span style='display: inline-block;transform: scaleX(-1)';>📡</span>…🤖</h2>
  """,
  )

  if device or CONFIG_:
    device = getDevice(device)

  if not device:
    dom.inner(
      target, "<h3>ERROR: Please launch the 'Config' application!</h3>"
    )
    raise SystemExit("Unable to connect to a device!")

  setDevice(device=device)

  start = time.monotonic()
  infos = getInfos(device)

  if (elapsed := time.monotonic() - start) < 3:
    time.sleep(3 - elapsed)

  deviceId = getDeviceId(infos)

  dom.inner(target, ATK_BODY_.format(infos[IK_KIT_LABEL], deviceId))

  dom.inner("ucuq_body", body)

  time.sleep(1.5)

  dom.inner(target, body)

  atlastk.setCallback(UCUQ_XDEVICE_ACTION_, handleXDeviceRetrieving_)

  return infos


def getDevice(device=None, *, id=None, token=None):
  if device and (token or id):
    displayExitMessage_("'device' can not be given together with 'token' or 'id'!")

  if device == None:
    global device_

    if token or id:
      device_ = Device(id=id, token=token)
    elif device_ == None:
      device_ = Device()
      device_.connect()
    return device_
  else:
    return device


def addCommand(command, commit=False, /, device=None):
  getDevice(device).addCommand(command, commit)


# does absolutely nothing whichever method is called but returns 'self'.
# for the handling of the 'extra' parameter in the init method, which handles extra initialisation.
class Nothing:
  def __getattr__(self, name):
    def doNothing(*args, **kwargs):
      return self

    return doNothing

  def __bool__(self):
    return False


# does absolutely nothing whichever method is called.
# 'if Nothing()' returns 'False'.
class Nothing_:
  def __init__(self, object):
    self.object = object

  def __getattr__(self, name):
    def doNothing(*args, **kwargs):
      return self.object

    return doNothing

  def __bool__(self):
    return False


class Core_:
  def __init__(self, device=None):
    self.id = None
    self.device_ = device

  def __del__(self):
    if self.id:
      self.addCommand(f"del {ITEMS_}[{self.id}]")

  def getDevice(self):
    return self.device_

  def getId(self):
    return self.id

  def init(self, modules, instanciation, device, extra, *, before=""):
    self.id = getObjectIndice()

    if self.device_:
      if device and device != self.device_:
        raise Exception("'device' already given!")
    else:
      self.device_ = getDevice(device)

    if modules:
      self.device_.addModules(modules)

    if before:
      self.addCommand(before)

    if instanciation:
      self.addCommand(f"{self.getObject()} = {instanciation}")

    return self if not isinstance(extra, bool) or extra else Nothing_(self)

  def getObject(self):
    return getObject_(self.id)

  def addCommand(self, command):
    self.device_.addCommand(command)
    return self

  def addMethods(self, methods):
    return self.addCommand(f"{self.getObject()}.{methods}")

  def callMethod(self, method):
    return self.device_.commit(f"{self.getObject()}.{method}")

  def sleepStart(self, id=None):
    return self.device_.sleepStart(id)

  def sleepWait(self, id, secs):
    self.device_.sleepWait(id, secs)
    return self

  def sleep(self, secs):
    self.device_.sleep(secs)
    return self


class GPIO(Core_):
  def __init__(self, pin=None, device=None, extra=True):
    super().__init__(device)

    if pin:
      self.init(pin, device, extra)

  def init(self, pin, device=None, extra=True):
    self.pin = f'"{pin}"' if isinstance(pin, str) else pin

    super().init("GPIO-1", f"GPIO({self.pin})", device, extra)

  def high(self, value=True):
    return self.addMethods(f"high({value})")

  def low(self):
    return self.high(False)


class I2C_Core_(Core_):
  def __init__(self, sda=None, scl=None, soft=None, *, device=None):
    super().__init__(device)

    if sda == None != scl == None:
      raise Exception("None or both of sda/scl must be given!")
    elif sda != None:
      self.init(sda, scl, soft=soft, device=device)

  def scan(self):
    return commit(f"{self.getObject()}.scan()")


class I2C(I2C_Core_):
  def init(self, sda, scl, soft=None, *, device=None, extra=True):
    if soft == None:
      soft = False

    super().init(
      "I2C-1",
      f"machine.{'Soft' if soft else ''}I2C({'0,' if not soft else ''} sda=machine.Pin({sda}), scl=machine.Pin({scl}))",
      device=device,
      extra=extra,
    )


class SoftI2C(I2C):
  def init(self, sda, scl, *, soft=None, device=None):
    if soft == None:
      soft = True

    super().init(sda, scl, soft=soft, device=device)


class SPI(Core_):
  def __init__(
    self,
    id,
    sck=None,
    mosi=None,
    miso=None,
    baudrate=None,
    *,
    polarity=None,
    phase=None,
    bits=None,
    device=None,
  ):
    super().__init__(device)

    if sck == None != mosi == None or sck == None != miso == None:
      raise Exception("None or all of sck/ mosi/ miso must be given!")
    elif sck != None:
      self.init(
        id,
        sck,
        mosi,
        miso,
        baudrate=baudrate,
        polarity=polarity,
        phase=phase,
        bits=bits,
        device=device,
      )

  def init(
    self,
    id,
    sck=None,
    mosi=None,
    miso=None,
    baudrate=None,
    polarity=None,
    phase=None,
    bits=None,
    device=None,
    extra=True,
  ):
    super().init(
      None,
      f"machine.{'Soft' if not id else ''}SPI({str(id) + ', ' if id else ''}sck=machine.Pin({sck}){getParam('mosi', mosi, 'machine.Pin({})')}{getParam('miso', miso, 'machine.Pin({})')}{getParam('baudrate', baudrate)}{getParam('polarity', polarity)}{getParam('phase', phase)}{getParam('bits', bits)})",
      device=device,
      extra=extra,
    )


class SoftSPI(SPI):
  def __init__(
    self,
    sck,
    mosi,
    miso,
    *,
    id=None,
    baudrate=None,
    polarity=None,
    phase=None,
    bits=None,
    device=None,
  ):
    super().__init__(
      id,
      sck,
      mosi,
      miso,
      baudrate=baudrate,
      polarity=polarity,
      phase=phase,
      bits=bits,
      device=device,
    )


class WS2812(Core_):
  def __init__(self, n=None, pin=None, device=None, extra=True):
    super().__init__(device)

    if (pin == None) != (n == None):
      raise Exception("Both or none of 'pin'/'n' must be given")

    if pin != None:
      self.init(n, pin, device=device, extra=extra)

  def init(self, n, pin, device=None, extra=True):
    super().init(
      "WS2812-1", f"neopixel.NeoPixel(machine.Pin({pin}), {n})", device, extra
    ).flash(extra)

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
    return self

  def flash(self, extra=True):
    self.fill((255, 255, 255)).write()
    self.getDevice().sleep(FLASH_DELAY_ if isinstance(extra, bool) else extra)
    return self.fill((0, 0, 0)).write()


class HT16K33(Core_):
  def __init__(self, i2c=None, addr=None, extra=True):
    super().__init__()

    if i2c:
      self.init(i2c, addr=addr, extra=extra)

  def init(self, i2c, addr=None, extra=True):
    return (
      super()
      .init(
        "HT16K33-1",
        f"HT16K33({i2c.getObject()}, {addr})",
        i2c.getDevice(),
        extra,
      )
      .setBrightness(15)
      .flash(extra)
      .setBrightness(0)
    )

  def flash(self, extra=True):
    self.draw("ffffffffffffffffffffffffffffffff")
    self.getDevice().sleep(FLASH_DELAY_ if isinstance(extra, bool) else extra)
    return self.draw("")

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

  def rect(self, x0, y0, x1, y1, ink=True):
    return self.addMethods(f"rect({x0}, {y0}, {x1}, {y1}, ink={1 if ink else 0})")

  def show(self):
    return self.addMethods(f"render()")


def getParam(label, value, expr=None):
  if value:
    return f", {label} = {value if expr is None else expr.format(value)}"
  else:
    return ""


class PWM(Core_):
  def __init__(
    self, pin=None, *, freq=None, ns=None, u16=None, device=None, extra=True
  ):
    super().__init__(device)

    if pin != None:
      self.init(pin, freq=freq, u16=u16, ns=ns, device=device, extra=extra)

  def init(self, pin, *, freq=None, u16=None, ns=None, device=None, extra=True):
    command = f"machine.PWM(machine.Pin({pin}, machine.Pin.OUT){getParam('freq', freq)}{getParam('duty_u16', u16)}{getParam('duty_ns', ns)})"
    super().init("PWM-1", command, device, extra, before=f"{command}.deinit()")

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
  def __init__(self, i2c=None, *, addr=None):
    super().__init__()

    if i2c:
      self.init(i2c, addr=addr)

  def init(self, i2c, addr=None):
    super().init(
      "PCA9685-1", f"PCA9685({i2c.getObject()}, {addr})", i2c.getDevice()
    )

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
  def __init__(self, pca=None, channel=None):
    super().__init__()

    if bool(pca) != (channel != None):
      raise Exception("Both or none of 'pca' and 'channel' must be given!")

    if pca:
      self.init(pca, channel)

  def init(self, pca, channel):
    super().init(
      "PWM_PCA9685-1",
      f"PWM_PCA9685({pca.getObject()}, {channel})",
      pca.getDevice(),
    )

    self.pca = pca  # Not used inside this object, but to avoid pca being destroyed by GC, as it is used on the µc.

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

  def getU16(self, u16=None):
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


class HD44780_I2C(Core_):
  def __init__(self, num_columns, num_lines, /, i2c, addr=None, extra=True):
    super().__init__()

    if i2c:
      self.init(num_columns, num_lines, i2c, addr=addr, extra=extra)
    elif addr != None:
      raise Exception("addr can not be given without i2c!")

  def init(self, num_columns, num_lines, i2c, addr=None, extra=True):
    return (
      super()
      .init(
        "HD44780_I2C-1",
        f"HD44780_I2C({i2c.getObject()},{num_lines},{num_columns},{addr})",
        i2c.getDevice(),
        extra,
      )
      .flash(extra)
    )

  def moveTo(self, x, y):
    return self.addMethods(f"move_to({x},{y})")

  def putString(self, string):
    return self.addMethods('putstr("{}")'.format(string.replace('"','\\"')))

  def clear(self):
    return self.addMethods("clear()")

  def showCursor(self, value=True):
    return self.addMethods("show_cursor()" if value else "hide_cursor()")

  def hideCursor(self):
    return self.showCursor(False)

  def blinkCursorOn(self, value=True):
    return self.addMethods("blink_cursor_on()" if value else "blink_cursor_off()")

  def blinkCursorOff(self):
    return self.blinkCursorOn(False)

  def displayOn(self, value=True):
    return self.addMethods("display_on()" if value else "display_off()")

  def displayOff(self):
    return self.displayOn(False)

  def backlightOn(self, value=True):
    return self.addMethods("backlight_on()" if value else "backlight_off()")

  def backlightOff(self):
    return self.backlightOn(False)

  def flash(self, extra=True):
    self.backlightOn()
    self.getDevice().sleep(FLASH_DELAY_ if isinstance(extra, bool) else extra)
    return self.backlightOff()


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

  def __init__(self, pwm=None, specs=None, /, *, tweak=None, domain=None):
    super().__init__()

    self.test_(specs, tweak, domain)

    if pwm:
      self.init(pwm, specs, tweak=tweak, domain=domain)

  def init(self, pwm, specs, tweak=None, domain=None, extra=True):
    super().init("Servo-1", "", pwm.getDevice(), extra)

    self.test_(specs, tweak, domain)

    if not tweak:
      tweak = self.Tweak(specs.range / 2, 0, False)

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

    u16 = (
      self.specs.min
      + (angle + self.tweak.angle)
      * (self.specs.max - self.specs.min)
      / self.specs.range
      + self.tweak.offset
    )

    if u16 > self.domain.max:
      u16 = self.domain.max
    elif u16 < self.domain.min:
      u16 = self.domain.min

    return int(u16)

  def dutyToAngle(self, duty):
    angle = (
      self.specs.range
      * (duty - self.tweak.offset - self.specs.min)
      / (self.specs.mas - self.specs.min)
    )

    if self.tweak.invert:
      angle = -angle

    return angle - self.tweak.angle

  def reset(self):
    self.setAngle(0)

  def getAngle(self):
    return self.dutyToAngle(self.pwm.getU16())

  def setAngle(self, angle):
    return self.pwm.setU16(self.angleToDuty(angle))


class OLED_(Core_):
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

  def pixel(self, x, y, col=1):
    return self.addMethods(f"pixel({x},{y},{col})")

  def scroll(self, dx, dy):
    return self.addMethods(f"scroll({dx},{dy})")

  def text(self, string, x, y, col=1):
    return self.addMethods(f"text('{string}',{x}, {y}, {col})")

  def hText(self, string, y, col=1, trueWidth=None):
    trueWidth = trueWidth or f"{self.getObject()}.width"
    return self.addMethods(
      f"text('{string}',max(( {trueWidth} - len('{string}' ) * 8) // 2, 0), {y}, {col})"
    )

  def rect(self, x, y, w, h, col, fill=True):
    return self.addMethods(f"rect({x},{y},{w},{h},{col},{fill})")

  def ellipse(self, x, y, rx, ry, col, fill=True):
    return self.addMethods(f"ellipse({x},{y},{rx},{ry},{col}, {fill})")

  def draw(self, pattern, width, ox=0, oy=0, mul=1):
    if width % 4:
      raise Exception("'width' must be a multiple of 4!")
    return self.addMethods(f"draw('{pattern}',{width},{ox},{oy},{mul})")

  def flash(self, extra=True):
    self.fill(1).show()
    self.getDevice().sleep(FLASH_DELAY_ if isinstance(extra, bool) else extra)
    return self.fill(0).show()


class SSD1306(OLED_):
  def rotate(self, rotate=True):
    return self.addMethods(f"rotate({rotate})")


class SSD1306_I2C(SSD1306):
  def __init__(
    self,
    width=None,
    height=None,
    /,
    i2c=None,
    addr=None,
    external_vcc=False,
    extra=True,
  ):
    super().__init__()

    if bool(width) != bool(height) != bool(i2c):
      raise Exception("All or none of width/height/i2c must be given!")
    elif width:
      self.init(
        width, height, i2c, external_vcc=external_vcc, addr=addr, extra=extra
      )
    elif addr:
      raise Exception("addr can not be given without i2c!")

  def init(self, width, height, /, i2c, external_vcc=False, addr=None, extra=True):
    super().init(
      "SSD1306_I2C-1",
      f"SSD1306_I2C({width}, {height}, {i2c.getObject()}, {addr}, {external_vcc})",
      i2c.getDevice(),
      extra,
    ).flash(extra if not isinstance(extra, bool) else 0.15)


class SH1106(OLED_):
  pass


class SH1106_I2C(SH1106):
  def __init__(
    self,
    width=None,
    height=None,
    /,
    i2c=None,
    addr=None,
    external_vcc=False,
    extra=True,
  ):
    super().__init__()

    if bool(width) != bool(height) != bool(i2c):
      raise Exception("All or none of width/height/i2c must be given!")
    elif width:
      self.init(
        width, height, i2c, external_vcc=external_vcc, addr=addr, extra=extra
      )
    elif addr:
      raise Exception("addr can not be given without i2c!")

  def init(self, width, height, /, i2c, external_vcc=False, addr=None, extra=True):
    super().init(
      "SH1106_I2C-1",
      f"SH1106_I2C({width}, {height}, {i2c.getObject()}, addr={addr}, external_vcc={external_vcc})",
      i2c.getDevice(),
      extra,
    ).flash(extra if not isinstance(extra, bool) else 0.15)


OD_SH1106_ = "SH1106"
OD_SSD1306_ = "SSD1306"


class OLED_I2C:
  def __new__(cls, driver, *args, **kwargs):
    if driver == OD_SH1106_:
      return SH1106_I2C(*args, **kwargs)
    elif driver == OD_SSD1306_:
      return SSD1306_I2C(*args, **kwargs)
    else:
      raise Exception(f"Unknown OLED driver {driver}!")


c_ = lambda color: f"color565({color})"
f_ = lambda function, fill: f"{'fill_' if fill else 'draw_'}{function}"


def zoom_rgb565_(raw_data, width, height, hzoom, vzoom):
  zoomed_width = width * hzoom
  zoomed_height = height * vzoom

  zoomed_data = bytearray(zoomed_width * zoomed_height * 2)

  for y in range(height):
    for x in range(width):
      idx_src = (y * width + x) * 2
      pixel = raw_data[idx_src : idx_src + 2]  # 2 octets RGB565

      x_start = x * hzoom
      y_start = y * vzoom

      for dy in range(vzoom):
        for dx in range(hzoom):
          x_dst = x_start + dx
          y_dst = y_start + dy
          idx_dst = (y_dst * zoomed_width + x_dst) * 2
          zoomed_data[idx_dst : idx_dst + 2] = pixel

  return bytes(zoomed_data)


class ILI9341(Core_):
  def __init__(
    self,
    width,
    height,
    /,
    rotation=0,
    dc=None,
    cs=None,
    rst=None,
    spi=None,
    extra=True,
  ):
    super().__init__()

    if (
      bool(width)
      != bool(height)
      != bool(spi)
      != bool(dc)
      != bool(cs)
      != bool(rst)
    ):
      raise Exception("All or none of width/height/spi/dc/cs/rst must be given!")
    elif width:
      self.init(
        width,
        height,
        rotation=rotation,
        spi=spi,
        dc=dc,
        cs=cs,
        rst=rst,
        extra=extra,
      )

  def init(
    self,
    width,
    height,
    /,
    rotation=0,
    spi=None,
    dc=None,
    cs=None,
    rst=None,
    extra=True,
  ):
    super().init(
      "ILI9341-1",
      f"ILI9341({spi.getObject()}, machine.Pin({cs}), machine.Pin({dc}), machine.Pin({rst}), {width}, {height}, {rotation})",
      spi.getDevice(),
      extra,
    )

  def on(self, value=True):
    return self.addMethods(f"display_{'on' if value else 'off'}()")

  def off(self):
    return self.on(False)

  def clear(self, color=0):
    return self.addMethods(f"clear(color565({color}))")

  def cleanup(self):
    return self.addMethods("cleanup()")

  def invert(self, value=True):
    return self.addMethods(f"invert({value})")

  def pixel(self, x, y, color):
    return self.addMethods(f"draw_pixel({x}, {y}, {c_(color)})")

  def hline(self, x, y, w, color):
    return self.addMethods(f"draw_hline({x}, {y}, {w}, {c_(color)})")

  def vline(self, x, y, h, color):
    return self.addMethods(f"draw_vline({x}, {y}, {h}, {c_(color)})")

  def line(self, x0, y0, x1, y1, color):
    return self.addMethods(f"draw_line({x0}, {y0}, {x1}, {y1}, {c_(color)})")

  def lines(self, coords, color):
    return self.addMethods(f"draw_lines([tuple(map(int, pair.split(','))) for pair in '{{';'.join(f\"{{x}},{{y}}\" for x,y in coords)}}'.split(';')], {c_(color)})")

  def rect(self, x, y, w, h, color, fill=True):
    return self.addMethods(
      f"{f_('rectangle', fill)}({x}, {y}, {w}, {h}, {c_(color)})"
    )

  def poly(self, sides, x0, y0, r, color, rotate=0, fill=True):
    return self.addMethods(
      f"{f_('polygon', fill)}({sides}, {x0}, {y0}, {r}, {c_(color)}, {rotate})"
    )

  def circle(self, x, y, r, color, fill=True):
    return self.addMethods(f"{f_('circle', fill)}({x}, {y}, {r}, {c_(color)})")

  def ellipse(self, x, y, rx, ry, color, fill=True):
    return self.addMethods(
      f"{f_('ellipse', fill)}({x}, {y}, {rx}, {ry}, {c_(color)})"
    )

  def text(self, x, y, text, color=255, bgcolor=0, rotate=0):
    return self.addMethods(
      f"draw_text8x8({x}, {y}, '{text}', {c_(color)}, {c_(bgcolor)}, {rotate})"
    )

  def draw(self, stream, width, height, speed=1, hzoom=1, vzoom=0):
    if vzoom == 0:
      vzoom = hzoom

    for i in range(height // speed):
      data = stream.read(width * 2 * speed)
      self.addMethods(
        f"draw('{base64.b64encode(zoom_rgb565_(data, width, speed, hzoom, vzoom)).decode('ascii')}',0, {i*speed*vzoom}, {width*hzoom}, {speed*vzoom})"
      )

    if remainder := height % speed:
      data = stream.read(width * 2 * remainder)
      self.addMethods(
        f"draw('{base64.b64encode(zoom_rgb565_(data, width, speed, hzoom, vzoom)).decode('ascii')}',0, {(height // speed) * speed*vzoom}, {width*hzoom}, {remainder*vzoom})"
      )

    return self


class SSD1680_SPI(OLED_):
  def __init__(self, cs, dc, rst, busy, spi, landscape=True):
    super().__init__()
    self.init(cs, dc, rst, busy, spi, landscape=landscape)

  def init(self, cs, dc, rst, busy, spi, landscape=False, extra=True):
    super().init(
      "SSD1680-1",
      f"SSD1680({spi.getObject()},machine.Pin({cs}, machine.Pin.OUT),machine.Pin({dc}, machine.Pin.OUT),{rst},machine.Pin({busy}, machine.Pin.IN),{landscape})",
      spi.getDevice(),
      extra,
    )
    self.addMethods("init()")

  def hText(self, *args, trueWidth=None, **kargs):
    return super().hText(*args, trueWidth=trueWidth or 250, **kargs)


def pwmJumps(jumps, step=100, delay=0.05):
  command = "pwmJumps([\n"

  for jump in jumps:
    command += f"\t[{jump[0].getObject()},{jump[1]}],\n"

  command += f"], {step}, {delay})"

  return command


def execute_(command, device):
  device.addModule("PWMJumps-1")
  device.addCommand(command)


def servoMoves(moves, step=100, delay=0.05):
  jumps = {}
  devices = {}
  commands = {}

  for move in moves:
    servo = move[0]
    key = id(servo.getDevice())

    if not key in devices:
      devices[key] = servo.getDevice()
      jumps[key] = []
      commands[key] = []

    jumps[key].append([servo.pwm, servo.angleToDuty(move[1])])

  for key in jumps:
    commands[key].append(pwmJumps(jumps[key], step, delay))

  for key in commands:
    for command in commands[key]:
      execute_(command, devices[key])


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
      return [i, 0, 0]
    case 1:
      return [i, i, 0]
    case 2:
      return [0, i, 0]
    case 3:
      return [0, i, i]
    case 4:
      return [0, 0, i]
    case 5:
      return [i, 0, i]


def rbShadeFade(variant, i, max):
  if i < max:
    return rbFade(variant, i, max, True)
  elif i > max * 6:
    return rbFade((variant + 5) % 6, i % max, max, False)
  else:
    return rbShade(variant + int((i - max) / max), i % max, max)


def setCommitBehavior(behavior):
  global defaultCommitBehavior_

  defaultCommitBehavior_ = behavior
