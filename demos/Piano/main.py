import os, sys

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend(("../..","../../atlastk.zip"))

import ucuq, atlastk, math

# Widgets
W_TARGET = "Target"
W_RATIO_SLIDE = "RatioSlide"
W_RATIO_VALUE = "RatioValue"

pwm = None
baseFreq = 440.0*math.pow(math.pow(2,1.0/12), -16)
ratio = 0.5
target = None

hardware = None

def turnMainOn(hardware):
  global pwm

  if hardware == None:
    raise Exception("Kit with no sound component!")
  
  pwm = ucuq.PWM(hardware["Pin"], freq=50, u16=0).setNS(0)


def atk(dom):
  global pwm, target, hardware

  infos = ucuq.ATKConnect(dom, BODY)

  if not pwm:
    hardware = ucuq.getKitHardware(infos)

    turnMainOn(ucuq.getHardware(hardware, "Buzzer"))

    if "Loudspeaker" in hardware:
      dom.disableElement("HideTarget")
      target = "Buzzer"
  elif target: 
    dom.setValue(W_TARGET, target)
    dom.disableElement("HideTarget")


def atkPlay(dom,id):
  freq = int(baseFreq*math.pow(math.pow(2,1.0/12), int(id)))
  pwm.setU16(int(ratio*65535))
  pwm.setFreq(freq)
  ucuq.sleep(.5)
  pwm.setU16(0)


def atkSetRatio(dom, id):
  global ratio

  ratio = float(dom.getValue(id))

  dom.setValue(W_RATIO_SLIDE if id == W_RATIO_VALUE else W_RATIO_SLIDE, ratio)


def atkSwitchTarget(dom, id):
  global target

  target = dom.getValue(id)

  turnMainOn(ucuq.getHardware(hardware, target))

with open('Body.html', 'r') as file:
  BODY = file.read()

with open('Head.html', 'r') as file:
  ATK_HEAD = file.read()

atlastk.launch(globals=globals())

