import os, sys

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend(("../..","../../atlastk.zip"))

import atlastk, ucuq, datetime, json

epaper = None

W_QRC_TEXT = "QRCText"

W_TXT_TEXT = "TXTText"
W_TXT_WIDTH = "TXTWidth"
W_TXT_X = "TXTX"
W_TXT_Y = "TXTY"
W_TXT_FONT_SIZE = "TXTFontSize"
W_TXT_FONT = "TXTFont"
W_TXT_CENTER_X = "TXTCenterX"
W_TXT_CENTER_Y = "TXTCenterY"
W_TXT_CANVAS = "TXTCanvas"

def txtUpdate(dom):
  text, x, y, width, font, fontSize, centerX, centerY = (dom.getValues((W_TXT_TEXT, W_TXT_X, W_TXT_Y, W_TXT_WIDTH, W_TXT_FONT, W_TXT_FONT_SIZE, W_TXT_CENTER_X, W_TXT_CENTER_Y))).values()

  coords = json.loads(dom.executeString(f"JSON.stringify(createTextCanvas('{W_TXT_CANVAS}','{text}', {x}, {y}, {width}, \"{font}\", {fontSize}, {centerX}, {centerY}));"))

  values = {W_TXT_X: coords['x'], W_TXT_Y: coords['y']}

  if centerX != "true":
    del values[W_TXT_X]
    
  if centerY != "true":
    del values[W_TXT_Y]

  if values:
    dom.setValues(values)


def atk(dom):
  global epaper

  ucuq.ATKConnect(dom, BODY)

  epaper = ucuq.SSD1680_SPI(7, 1, 2, 3, ucuq.SPI(1, baudrate=2000000, polarity=0, phase=0, sck=4, mosi=6))
  # epaper = ucuq.SSD1680_SPI( cs=45, dc=46, rst=47, busy=48, spi=ucuq.SPI(1, baudrate=2000000, polarity=0, phase=0, sck=12, mosi=11)  )
  epaper.fill(0).hText("E-paper ready !", 50).hText(datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"), 75).show()

  dom.focus(W_QRC_TEXT)
  txtUpdate(dom)


# Called from JS!
def atkDisplay(dom, data):
  image = json.loads(data)
  
  epaper.fill(0).draw(image["pattern"], width = image['width'], ox = image['offsetX'], oy = image['offsetY'], mul = image['mul']).show()


def atkQRCSubmit(dom):
  dom.executeVoid(f"QRCodeLaunch('{dom.getValue(W_QRC_TEXT)}')")
  dom.focus(W_QRC_TEXT)


def atkQRCClear(dom):
  dom.setValue(W_QRC_TEXT, "")
  dom.focus(W_QRC_TEXT)


def atkTXTUpdate(dom):
  txtUpdate(dom)


def atkTXTSubmit(dom):
  text, x, y, width, font, fontSize, centerX, centerY = (dom.getValues((W_TXT_TEXT, W_TXT_X, W_TXT_Y, W_TXT_WIDTH, W_TXT_FONT, W_TXT_FONT_SIZE, W_TXT_CENTER_X, W_TXT_CENTER_Y))).values()

  dom.executeVoid(f"displayText('{W_TXT_CANVAS}','{text}', {x}, {y}, {width}, \"{font}\", {fontSize}, {centerX}, {centerY})")


def atkTXTClear(dom):
  dom.setValue(W_TXT_TEXT, "")


def atkTXTCenterX(dom, id):
  if ( ( dom.getValue(id) ) == "true"):
    dom.disableElement(W_TXT_X)
    txtUpdate(dom)
  else:
    dom.enableElement(W_TXT_X)


def atkTXTCenterY(dom, id):
  if ( ( dom.getValue(id) ) == "true"):
    dom.disableElement(W_TXT_Y)
    txtUpdate(dom)
  else:
    dom.enableElement(W_TXT_Y)


def atkReset(dom, id):
  global epaper
  epaper = ucuq.SSD1680_SPI(7, 1, 2, 3, ucuq.SPI(1, baudrate=2000000, polarity=0, phase=0, sck=4, mosi=6)).fill(0).show()
#  ucuq.SSD1680_SPI(cs=45, dc=46, rst=47, busy=48,spi=ucuq.SPI(1,baudrate=2000000, polarity=0, phase=0, sck=12, mosi=11)).fill(0).show()

with open('Body.html', 'r') as file:
  BODY = file.read()

with open('Head.html', 'r') as file:
  ATK_HEAD = file.read()

atlastk.launch(globals=globals())

