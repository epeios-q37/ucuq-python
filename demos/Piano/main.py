import os, sys

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend(("../..","../../atlastk.zip"))

import ucuq, atlastk, math

# Widgets
W_TARGET = "Target"
W_RATIO_SLIDE = "RatioSlide"
W_RATIO_VALUE = "RatioValue"

buzzer = None
loudspeaker = None
generator = None
baseFreq = 440.0*math.pow(math.pow(2,1.0/12), -16)
ratio = 0.5

def atk(dom):
  global buzzer, loudspeaker, generator

  infos = ucuq.ATKConnect(dom, BODY)

  if not generator:
    _, buzzer, loudspeaker = ucuq.getBits(infos, ucuq.B_BUZZER, ucuq.B_LOUDSPEAKER)

    generator = buzzer

    generator.setNS(0)

  if loudspeaker:
      loudspeaker.setNS(0)
      dom.disableElement("HideTarget")

  dom.setValue(W_TARGET, "Buzzer" if generator == buzzer else "Loudspeaker")


def atkPlay(dom,id):
  freq = int(baseFreq*math.pow(math.pow(2,1.0/12), int(id)))
  generator.setFreq(freq).setU16(int(ratio*65535))
  ucuq.sleep(.5)
  generator.setU16(0)


def atkSetRatio(dom, id):
  global ratio

  ratio = float(dom.getValue(id))

  dom.setValue(W_RATIO_SLIDE if id == W_RATIO_VALUE else W_RATIO_SLIDE, ratio)


def atkSwitchTarget(dom, id):
  global generator
  generator = buzzer if ( dom.getValue(id) ) == "Buzzer" else loudspeaker

with open('Body.html', 'r') as file:
  BODY = file.read()

with open('Head.html', 'r') as file:
  ATK_HEAD = file.read()

atlastk.launch(globals=globals())

