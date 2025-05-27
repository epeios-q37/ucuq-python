import os, sys

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend(("../..","../../atlastk.zip"))

import os, sys, json

import atlastk

# Languages
L_FR = 0
L_EN = 1

ATK_L10N = (
  (
    "en",
    "fr"
  ),
  (
    "Show/hide proxy settings",
    "Afficher/Masquer réglages proxy"
  ),
  (
    "Save",
    "Sauver"
  ),
  (
    "Delete",
    "Effacer"
  ),
  (
    "Enter <em>Token</em> and/or <em>Id</em>",
    "Saisir <em>Token</em> et/ou <em>Id</em>."
  ),
  (
    "Please enter a value for <em>Token</em>!",
    "Veuillez saisir une value pour <em>Token</em> !"
  ),
  (
    "Please enter a value for <em>Port</em>!",
    "Veuillez saisir une value pour <em>Port</em> !"
  ),
  (
    "Please enter a value for <em>Host</em>!",
    "Veuillez saisir une value pour <em>Host</em> !"
  ),
  (
    "Config file updated!",
    "Fichier de configuration mis à jour !"
  ),
  (
    "Deleting config file is not possible in development mode!",
    "Effacer le fichier de configuration n'est pas possible en mode développement !"
  ),
  (
    "Are you sure you want to delete config file?",
    "Êtes-vous sûr de vouloir supprimer le fichier de configuration ?"
  ),
  (
    "Config file deleted!",
    "Fichier de configuration supprimé !"
  )
)

def isDev():
  return atlastk.isDev()


CONFIG_FILE = ( "/home/csimon/q37/epeios/other/BPY/Apps/UCUq/" if isDev() else "../" ) + "ucuq.json"


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

DEFAULT_PROXY_HOST = "ucuq.q37.info"
DEFAULT_PROXY_PORT = "53843"
DEFAULT_PROXY_SSL = True

# Keys
K_DEVICE = "Device"
K_DEVICE_TOKEN = "Token"
K_DEVICE_ID = "Id"
K_PROXY = "Proxy"
K_PROXY_HOST = "Host"
K_PROXY_PORT = "Port"
K_PROXY_SSL = "SSL"

# Widgets
W_PROXY = "Proxy"
W_HOST = "Host"
W_PORT = "Port"
W_SSL = "SSL"
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

  proxyConfig = getConfigProxy()

  if K_PROXY_HOST in proxyConfig:
    values[W_HOST] = proxyConfig[K_PROXY_HOST]
  else:
    setAsHidden(dom, W_HOST)

  if K_PROXY_PORT in proxyConfig:
    values[W_PORT] = proxyConfig[K_PROXY_PORT]
  else:
    setAsHidden(dom, W_PORT)

  if K_PROXY_SSL in proxyConfig:
    values[W_SSL] = "true" if proxyConfig[K_PROXY_SSL] else "false"

  device = getConfigDevice()

  if K_DEVICE_TOKEN in device:
    setAsHidden(dom, W_TOKEN)

  if K_DEVICE_ID in device:
    values[W_ID] = device[K_DEVICE_ID]

  if values:
    dom.setValues(values)

  dom.focus(W_TOKEN if not K_DEVICE_TOKEN in device else W_ID)


def atk(dom):
  dom.inner("", BODY.format(**dom.getL10n(proxy=1, save=2, delete=3, hint=4)))

  dom.disableElement(S_HIDE_PROXY)

  updateUI(dom)


def atkSave(dom):
  host, port, ssl, token, id = (value.strip() for value in (dom.getValues([W_HOST, W_PORT, W_SSL, W_TOKEN, W_ID])).values())

  ssl = True if ssl == "true" else False

  device = getConfigDevice()

  if not token and K_DEVICE_TOKEN not in device:
    dom.alert(dom.getL10n(5))
    dom.focus(W_TOKEN)
    return

  if token:
    device[K_DEVICE_TOKEN] = token

  if id:
    device[K_DEVICE_ID] = id

  proxyConfig = getConfigProxy()

  if not host and not port:
    proxyConfig = None
  else:
    if host:
      if not port:
        dom.alert(dom.getL10N(6))
        dom.focus(W_PORT)
        return
    elif port:
      if not host:
        dom.alert(dom.getL10n(7))
        dom.focus(W_HOST)
        return

    proxyConfig[K_PROXY_HOST] = host
    proxyConfig[K_PROXY_PORT] = port
    proxyConfig[K_PROXY_SSL] = ssl
    
  config = getConfig()

  config[K_DEVICE] = device

  if proxyConfig:
    config[K_PROXY] = proxyConfig
  elif K_PROXY in config:
    del config[K_PROXY]

  save(config)

  dom.setValue(W_OUTPUT, dom.getL10n(8))


def atkDelete(dom):
  if isDev():
    dom.alert(dom.getL10n(9))
  elif dom.confirm(dom.getL10n(10)):
    delete()
    dom.removeAttribute(W_TOKEN, "placeholder")
    dom.setValues({W_TOKEN: "", "Id": ""})
    dom.focus(W_TOKEN)
    dom.setValue(W_OUTPUT, dom.getL10n(11))


with open('Body.html', 'r') as file:
  BODY = file.read()

with open('Head.html', 'r') as file:
  ATK_HEAD = file.read()

atlastk.launch(globals=globals())

