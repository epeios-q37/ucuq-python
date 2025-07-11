import os, sys

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend(("../..","../../atlastk.zip"))

import os, sys, zlib, base64

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.append("../../atlastk")

import atlastk, ucuq

from random import randint

UCUQ = True

L_FR = 0
L_EN = 1

ATK_L10N = (
  (
    "en",
    "fr"
  ),
  (
    "You've run out of guesses!",
    "Vous êtes à court d'essais !",
  ),
  (
    "You had {errors} errors and {correct} correct guesses.",
    "Vous avez fait {errors} erreurs et trouvé {correct} bonnes lettres.",
  ),
  (
    "The world was '{}'.",
    "Le mot était '{}'.",
  ),
  (
    "Congratulations!",
    "Bravo !",
  ),
  (
    "You've won! Congratulations!",
    "Vous avez gagné ! Félicitations !",
  ),
  (
    "Restart",
    "Recommencer",
  )
)

DICTIONARY_EN = (
  "apple", "banana", "grape", "orange", "mango", "peach", "pineapple", "strawberry",
  "blueberry", "blackberry", "kiwi", "melon", "pear", "plum", "cherry", "coconut",
  "watermelon", "papaya", "apricot", "lemon", "lime", "pomegranate", "fig", "date",
  "tomato", "cucumber", "carrot", "potato", "onion", "garlic", "pepper", "spinach",
  "lettuce", "broccoli", "cabbage", "celery", "zucchini", "eggplant", "beet", "radish",
  "turnip", "squash", "pumpkin", "asparagus", "artichoke", "parsley", "basil", "oregano",
  "cilantro", "thyme", "rosemary", "sage", "chili", "cinnamon", "ginger", "nutmeg",
  "vanilla", "peppermint", "cardamom", "anise", "clove", "fennel", "cumin", "coriander",
  "mustard", "sesame", "sunflower", "almond", "walnut", "pecan", "hazelnut", "cashew",
  "pistachio", "peanut", "grain", "barley", "oat", "wheat", "rice", "quinoa",
  "corn", "millet", "sorghum", "rye", "buckwheat", "spelt", "farro", "teff",
  "chickpea", "lentil", "kidney", "blackbean", "soybean", "pinto", "tofu", "tempeh",
  "seitan", "vegan", "vegetarian", "carnivore", "omnivore", "sustainable", "organic"
)

DICTIONARY_FR = (
  "abondant", "bateau", "chien", "dormir", "fleur", "gantier", "hiver",
  "jardin", "kiwi", "lune", "maison", "nuage", "oiseau", "plage",
  "quai", "rire", "soleil", "table", "usine", "verre", "wagon", "hippopotame",
  "arbre", "bonheur", "ciel", "danse", "feuille", "guitare", "herbe",
  "insecte", "jouet", "livre", "montagne", "neige", "glacier", "pluie",
  "question", "sable", "train", "univers", "vent", "whisky", "avion",
  "ballon", "chapeau", "drapeau", "foret", "glace", "horloge", "igloo",
  "kayak", "lampe", "musique", "nuit", "papillon", "radio", "stylo",
  "voiture", "amour", "biscuit", "cacao", "dent", "fromage", "graine",
  "hibou", "image", "jupe", "koala", "lait", "miel", "orange", "pomme",
  "quiche", "rose", "sucre", "tomate", "violon", "yaourt", "abeille",
  "banane", "carotte", "dauphin", "fraise", "gorille", "hamster",
  "igname", "jonquille", "kiosque", "lavande", "mouton", "narcisse",
  "poire", "renard", "serpent", "tulipe", "valise", "wasabi", "xylophone",
  "yoga", "zeste", "abricot", "bambou", "cactus", "dahlia", "framboise",
  "gantier", "hautbois", "jardinier", "kiosquier", "laurier", "magnolia",
  "mouvement", "nation", "nature", "nuageux", "paysage", "chasseur", "petit",
  "pouvoir", "rapport", "region", "ramification", "retour", "cauchemar", "rivage",
  "saison", "sang", "sauvetage", "secours", "sentier", "film", "service",
  "situation", "village", "spectacle", "sport", "station", "style", "appareil",
  "tendance", "terrain", "concert", "tourisme", "travail", "tribunal", "colifichet"
)

DICTIONARIES = (
  DICTIONARY_FR,
  DICTIONARY_EN
)

BUZZER_SCRIPT = f"""
def buzz_(buzzer, freq, secs):
  buzzer.freq(freq)
  buzzer.duty_u16(50000)
  {"aw"}{"ait"} asyncio.sleep(secs)
  buzzer.duty_u16(0)

def buzz(buzzer, freq, secs):
  asyncio.create_task(buzz_(buzzer, freq, secs))
"""

HANGED_MAN = "Head Body LeftArm RightArm LeftLeg RightLeg".split()

unpack = lambda data : zlib.decompress(base64.b64decode(data)).decode()

START_PATTERN = unpack("eJwzMDBPA4NUAyBAZpsZGMApOrENRtmjbNqw03AAACZsma8=")

HANGED_MAN_PATTERNS = (
  unpack("eJwzMDBPA4NUAyBAZpsZGMApKrPTEGzjtGQ429wgFc42A9MQdrKBMUlsZL3IZiLbhewGJAeOsocpOw0HAAAjmpxP"),
  unpack("eJwzMDBPA4NUAyBAZpsZGMApKrPTEGzjtGQ429wgFc42A9MQdrKBMUlsZL3IZiLbhewGmvhxsLENRjY7DQcAANVInME="),
  unpack("eJzl0EEKgDAMRNErjRSS3ic09z+CUiH+TUFBV84mb9FOQyXPmaEjtEk1XnZebhll1yjbnKdD7ZF5l518izvc2tnpjjPoNIMbvHV0Bmyf/jOtfzsX2QG1wJ1J"),
  unpack("eJzlkDEOwCAMA79khGTyH0T+/4SitApeGJDaqV58C+YUoHlkYEaZQNbL7Iur9+SGkczomzvqEetb3dS/1OHUubitTa5NUpyZPsVY7OE6q+dwiH54Z2X8m32TC+KXnfY="),
  unpack("eJzF0EEKwCAMBMAvbQhE/yPm/0+oWInbYg9CS3PJXIybAMl7VbRiGxDtZfu0egkn1LD1frpAt8xveSb/xRl2M4vnOdPmTDPKbJFHskke1tZKDO5BP7xzIkteG3QTutvVSo5dbo69xuOl8Zf9oQ5w1p6c"),
  unpack("eJy9kEEOwCAIBL+0hoTS9xj5/xNqbAN70INJIxfmoMsAcPmohl7MCkT7mT1ZvAZfaME6+ssVssX8lzN5FjvsOhe3zNTMVCVnDZ9iWuxj6a1G8BA9c+dy25QF5E93W9y/LxK7MMt4lsN1wiDB4+yLegALt59A"),
)

HAPPY_PATTERN = "03c00c30181820044c32524a80018001824181814812442223c410080c3003c0"

COUNTER_LEDS = (5,6,7,1,2,3)

FIXED_LEDS = (4,0)

normalize = lambda string : string.ljust(16) if len(string) < 16 else string[-16:]

class HW:
  def __init__(self, hwDesc):
    self.lcd = ucuq.HD44780_I2C(16, 2, ucuq.I2C(*ucuq.getHardware(hwDesc, "LCD", ["SDA", "SCL", "Soft"]))).backlightOn()
    self.oled =  ucuq.SSD1306_I2C(128, 64, ucuq.I2C(*ucuq.getHardware(hwDesc, "OLED", ["SDA", "SCL", "Soft"])))
    self.buzzer = ucuq.PWM(*ucuq.getHardware(hwDesc, "Buzzer", ["Pin"]), freq=50, u16 = 0).setNS(0)
    pin, self.ringCount, self.ringOffset, self.ringLimiter = ucuq.getHardware(hwDesc, "Ring", ["Pin", "Count", "Offset", "Limiter"])
    self.ring = ucuq.WS2812(pin, self.ringCount)

  def ringPatchIndex_(self, index):
    return ( index + self.ringOffset ) % self.ringCount
  
  def update(self, errors):
    for e in range(errors+1):
      self.ring.setValue(self.ringPatchIndex_(COUNTER_LEDS[e-1]), [self.ringLimiter, 0, 0])

    for e in range(errors+1, 7):
      self.ring.setValue(self.ringPatchIndex_(COUNTER_LEDS[e-1]), [0, self.ringLimiter, 0])

    for l in FIXED_LEDS:
      self.ring.setValue(self.ringPatchIndex_(l), [self.ringLimiter * errors // 6, 0, self.ringLimiter * ( 6 - errors ) // 6])

    self.ring.write()

    if (errors):
      self.oled.draw(HANGED_MAN_PATTERNS[errors-1],48, ox=47).show()

  def lcdPutString(self, x, y, string):
    self.lcd.moveTo(x,y).putString(string)

  def restart(self):
    self.oled.fill(0).draw(START_PATTERN, 48, ox=47).show()
    self.lcdPutString(0,1, normalize(""))

  def success(self, message):
    self.lcd.moveTo(0,1).putString(message)
    self.oled.draw(HAPPY_PATTERN, 16, mul=4, ox=32).show()
    for _ in range(3):
      for l in range(self.ringCount):
        self.ring.setValue(self.ringPatchIndex_(l), tuple(map(lambda _: randint(0,self.ringLimiter // 3), range(3)))).write()
        ucuq.sleep(0.075)

  def buzz(self):
    ucuq.addCommand(f"buzz({self.buzzer.getObject()}, 50, 0.5)")

class Core:
  def reset(self):
    self.errors = 0
    self.correctGuesses = []
    self.secretWord = ""
    self.chosen = ""

  def __init__(self):
    self.reset()

hw = None

def randword(dictionnary):
  return dictionnary[randint(0, len(dictionnary)-1)]


def update(dom, errors):
  hw.update(errors)

  if (errors):
    dom.removeClass(HANGED_MAN[errors-1], "hidden")


def showWord(dom, secretWord, correctGuesses):
  output = ("_" * len(secretWord))
  
  for i in range(len(secretWord)):
    if secretWord[i] in correctGuesses:
      output = output[:i] + secretWord[i] + output[i + 1:]

  hw.lcdPutString(0,0,output.center(16))

  html = atlastk.createHTML()
  html.putTagAndValue("h1", output)
  dom.inner("output", html)


def reset(core, dom):
  core.reset()
  dom.inner("", BODY.format(**dom.getL10n(restart=6)))
  language = L_FR if dom.language.startswith("fr") else L_EN
  core.secretWord = randword(DICTIONARIES[language])
  print(core.secretWord)
  hw.restart()
  showWord(dom, core.secretWord, core.correctGuesses)
  update(dom, 0)


def atk(core, dom):
  global hw

  if UCUQ:
    if not hw:
      infos = ucuq.ATKConnect(dom, "")
      hw = HW(ucuq.getKitHardware(infos))
  else:
    hw = ucuq.Nothing()

  ucuq.addCommand(BUZZER_SCRIPT)

  reset(core,dom)


def atkSubmit(core, dom, id):
  dom.addClass(id, "chosen")

  guess = id.lower()
  core.chosen += guess

  if guess in core.secretWord:
    core.correctGuesses.append(guess)

    correct = 0

    for i in range(len(core.secretWord)):
      if core.secretWord[i] in core.correctGuesses:
        correct += 1

    showWord(dom, core.secretWord, core.correctGuesses)

    if correct == len(core.secretWord):
      hw.success(dom.getL10n(4))
      dom.alert(dom.getL10n(5))
      reset(core, dom)
      return
  else:
    hw.buzz()
    core.errors += 1
    hw.lcdPutString(0,1,normalize(''.join([char for char in core.chosen if char not in core.correctGuesses])))
    update(dom, core.errors)

  
  if core.errors >= len(HANGED_MAN):
    dom.removeClass("Face", "hidden")
    showWord(dom, core.secretWord, core.secretWord)
    dom.alert(f"{dom.getL10n(1)}\n{dom.getL10n(2).format(errors=core.errors, correct=len(core.correctGuesses))}\n\n{dom.getL10n(3).format(core.secretWord)}")
    reset(core, dom)


def atkRestart(core, dom):
  if (core.secretWord != "" ):
    dom.alert(f"{dom.getL10n(2).format( errors=core.errors, correct=len(core.correctGuesses))}\n\n{dom.getL10n(3).format(core.secretWord)}")

  reset(core, dom)

ATK_USER = Core

with open('Body.html', 'r') as file:
  BODY = file.read()

with open('Head.html', 'r') as file:
  ATK_HEAD = file.read()

atlastk.launch(globals=globals())

