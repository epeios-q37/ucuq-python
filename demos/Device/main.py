import os, sys

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend(("../..","../../atlastk.zip"))

import atlastk, ucuq, json

def acConnect(dom):
  infos = ucuq.ATKConnect(dom, BODY)
  dom.setValue("Infos", json.dumps(infos, indent=2))

CALLBACKS = {
  "": acConnect
}

with open('Body.html', 'r') as file:
  BODY = file.read()

with open('Head.html', 'r') as file:
  HEAD = file.read()

atlastk.launch(CALLBACKS if "CALLBACKS" in globals() else None, globals=globals(), headContent=HEAD)

