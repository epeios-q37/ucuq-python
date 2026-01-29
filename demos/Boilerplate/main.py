import os, sys

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend(("../..","../../atlastk.zip"))

import ucuq, atlastk

def atk(dom):
  ucuq.ATKConnect(dom, BODY)
  ucuq.GPIO(8).high()
  
def atkSwitch(dom, id):
  ucuq.GPIO(8).high(dom.getValue(id) != "true")

with open('Body.html', 'r') as file:
  BODY = file.read()

with open('Head.html', 'r') as file:
  ATK_HEAD = file.read()

atlastk.launch(globals=globals())

