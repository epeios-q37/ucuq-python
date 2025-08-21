import os, sys

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend(("../..","../../atlastk.zip"))

import atlastk, ucuq, datetime, time

epaper = None

W_TEXT = "Text"

def atk(dom):
  global epaper

  ucuq.ATKConnect(dom, BODY)
  epaper = ucuq.SSD1680_SPI(7, 1, 2, 3, ucuq.SPI(1, baudrate=2000000, polarity=0, phase=0, sck=4, mosi=6))
  epaper.fill(0).hText("E-paper ready !", 50).hText(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"), 75).show()
  dom.focus(W_TEXT)

# Called from JS!
def atkDisplay(dom, id):
  epaper.fill(0).draw(id, ox=60, oy=6, width=120).show()


def atkSubmit(dom):
  dom.executeVoid(f"generate('{dom.getValue(W_TEXT)}')")
  dom.focus(W_TEXT)


def atkClear(dom):
  dom.setValue(W_TEXT, "")
  dom.focus(W_TEXT)


def atkReset(dom, id):
  global epaper
  epaper = ucuq.SSD1680_SPI(7, 1, 2, 3, ucuq.SPI(1, baudrate=2000000, polarity=0, phase=0, sck=4, mosi=6)).fill(0).show()


with open('Body.html', 'r') as file:
  BODY = file.read()

with open('Head.html', 'r') as file:
  ATK_HEAD = file.read()

atlastk.launch(globals=globals())

