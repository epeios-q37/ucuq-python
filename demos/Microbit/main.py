import os, sys

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend(("../..","../../atlastk.zip"))

import ucuq, atlastk

microbit = ucuq.Microbit()


def atk(dom):
  dom.inner("", BODY)  # type: ignore # noqa: F821
  
  
def clear(dom):
  microbit.clear()
  dom.executeVoid('clearMatrix()')
  

def atkSelect(dom, id):
  pos = int(dom.executeString(f'getPosition("{id}")'))
  
  x = pos // 5
  y = pos % 5
  
  microbit.setPixel(x, y, level :=  (0 if microbit.getPixel(x, y) else 9))
  
  dom.setAttribute(id, "style", f"opacity: {0 if level == 0 else 1}")


def atkSubmit(dom):
  clear(dom)
  microbit.showText(dom.getValue("Text"))
  
  

def atkTest(dom):
  clear(dom)
  dom.executeVoid('clearMatrix()')
  microbit.flash()
  

with open('Body.html', 'r') as file:
  BODY = file.read()

with open('Head.html', 'r') as file:
  ATK_HEAD = file.read()

atlastk.launch(globals=globals())

