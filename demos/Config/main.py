import os, sys

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend(("../..","../../atlastk.zip"))

import os, sys, json

import atlastk


def isDev():
  return "Q37_EPEIOS" in os.environ

CONFIG_FILE = ( "/home/csimon/q37/epeios/tools/ucuq/remote/wrappers/PYH/" if isDev() else "../" ) + "ucuq.json"


def getConfig():
  if os.path.isfile(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as file:
      return json.load(file)
  else:
    return {
      K_DEVICE: {},
      K_PROXY: {}
    }
  

def save(config):
  with open(CONFIG_FILE, "w") as file:
    json.dump(config, file, indent=2)


def delete():
    os.remove(CONFIG_FILE)

DEFAULT_HOST = "ucuq.q37.info"
DEFAULT_PORT = "53800"

# Keys
K_DEVICE = "Device"
K_DEVICE_TOKEN = "Token"
K_DEVICE_ID = "Id"
K_PROXY = "Proxy"
K_PROXY_HOST = "Host"
K_PROXY_PORT = "Port"

# Widgets
W_PROXY = "Proxy"
W_HOST = "Host"
W_PORT = "Port"
W_TOKEN = "Token"
W_ID = "Id"
W_OUTPUT = "Output"

# Style
S_HIDE_PROXY = "HideProxy"


def getConfigProxy():
  config = getConfig()

  if K_PROXY in config:
    return config[K_PROXY]
  else:
    return {}


def getConfigDevice():
  return getConfig()[K_DEVICE]


def setAsHidden(dom, id):
  dom.setAttribute(id, "placeholder", "<hidden>")


def updateUI(dom):
  values = {}

  proxy = getConfigProxy()

  if K_PROXY_HOST in proxy:
    values[W_HOST] = proxy[K_PROXY_HOST]
  else:
    setAsHidden(dom, W_HOST)

  if K_PROXY_PORT in proxy:
    values[W_PORT] = proxy[K_PROXY_PORT]
  else:
    setAsHidden(dom, W_PORT)

  device = getConfigDevice()

  if K_DEVICE_TOKEN in device:
    setAsHidden(dom, W_TOKEN)

  if K_DEVICE_ID in device:
    values[W_ID] = device[K_DEVICE_ID]

  if values:
    dom.setValues(values)

  dom.focus(W_TOKEN if not K_DEVICE_TOKEN in device else W_ID)


def atk(dom):
  dom.inner("", BODY)

  dom.disableElement(S_HIDE_PROXY)

  updateUI(dom)


def atkSave(dom):
  host, port, token, id = (value.strip() for value in (dom.getValues([W_HOST, W_PORT, W_TOKEN, W_ID])).values())

  device = getConfigDevice()

  if not token and K_DEVICE_TOKEN not in device:
    dom.alert("Please enter a token value!")
    dom.focus(W_TOKEN)
    return

  if token:
    device[K_DEVICE_TOKEN] = token

  if id:
    device[K_DEVICE_ID] = id

  proxy = getConfigProxy()

  if not host and not port:
    proxy = None
  elif host:
    if not port:
      dom.alert("Please enter a port!")
      dom.focus(W_PORT)
      return

    proxy[K_PROXY_HOST] = host
  elif port:
    if not host:
      dom.alert("Please enter a host!")
      dom.focus(W_HOST)
      return
    
  config = getConfig()

  config[K_DEVICE] = device

  if proxy:
    config[K_PROXY] = proxy
  else:
    del config[K_PROXY]

  save(config)

  dom.setValue(W_OUTPUT, "Config file updated!")


def atkDelete(dom):
  if isDev():
    dom.alert("You are in development environment, deleting config file is not possible!")
  elif dom.confirm("Are you sure you want to delete config file ?"):
    delete()
    dom.removeAttribute(W_TOKEN, "placeholder")
    dom.setValues({W_TOKEN: "", "Id": ""})
    dom.focus(W_TOKEN)
    dom.setValue(W_OUTPUT, "Config deleted!")


with open('Body.html', 'r') as file:
  BODY = file.read()

with open('Head.html', 'r') as file:
  ATK_HEAD = file.read()

atlastk.launch(globals=globals())

