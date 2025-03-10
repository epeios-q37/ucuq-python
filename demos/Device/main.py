import os, sys

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend(("../..","../../atlastk.zip"))

import atlastk, ucuq, json

def atk(dom):
  infos = ucuq.ATKConnect(dom, BODY)
  dom.setValue("Infos", json.dumps(infos, indent=2))

with open('Body.html', 'r') as file:
  BODY = file.read()

with open('Head.html', 'r') as file:
  ATK_HEAD = file.read()

atlastk.launch(globals=globals())

