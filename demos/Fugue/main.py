import os, sys

os.chdir(os.path.dirname(os.path.realpath(__file__)))
sys.path.extend(("../..","../../atlastk.zip"))

import ucuq, random, time, gc, zlib, base64

DEVICES = ("","India", "Lima")

RGB_MAX = 15


def rainbow(n, max):
  colors = []
  
  for i in range(n):
    h = (i * 6) / n
    x = int((1 - abs((h % 2) - 1)) * max)

    if   0 <= h < 1: r, g, b = max, x, 0
    elif 1 <= h < 2: r, g, b = x, max, 0
    elif 2 <= h < 3: r, g, b = 0, max, x
    elif 3 <= h < 4: r, g, b = 0, x, max
    elif 4 <= h < 5: r, g, b = x, 0, max
    else:            r, g, b = max, 0, x

    colors.append((r, g, b))
  return colors

RAINBOW = rainbow(30, RGB_MAX)

class RGB(ucuq.WS2812):
  def setValue(self, index, color = None):
    if not self.go:
      return self
    if color is None:
      color = RAINBOW[indexes[self.turn] % len(RAINBOW)]
    return super().setValue(index, color)


indexes = [random.randrange(len(RAINBOW)) for i in range(3)]
prev = [None] * 3


def sleepUntil(timestamp):
  ucuq.ntpSleepUntil(int(timestamp * 1_000_000))    


def scroll(text, start):
  width = len(lcds) * 16
  resizedText = " " * width + text + " " * width
  
  for s in range(64):
    oleds.scroll(0, 1).hline(0,0,64, 0).show()
    i = (len(resizedText) - width + 1) * s // 63
    sleepUntil(start)
    for l in range(len(lcds)):
      subText = resizedText[i + l * 16:i + (l + 1) * 16]
      lcds[l].moveTo(0,0).putString(subText)
      if not all(c == ' ' for c in subText):
        lcds[l].backlightOn()
      else:
        lcds[l].backlightOff()
    start += .13


def callback(_, events, duration):
  global timestamp
  
  sleepUntil(timestamp)

  for event in events:
    turn = event[0]
    buzzer = buzzers[turn]
    
    if event[1] != 0 and prev[turn] == event[1]:
      buzzer.off()
      oleds[turn].contrast(0)
    else:
      prev[turn] = event[1]
  
    if event[1] != 0:
      buzzer.play(int(event[1]))
      indexes[turn] += 1
      rgbs[turn].go = True
      oleds[turn].contrast(1)
    else:
      buzzer.off()
      oleds[turn].contrast(0)
      
    spots = MAP[turn]
    
    for spot in spots:
      rgbs.setValue(spot, (0,0,0))
      if event[1] != 0:
        rgbs.setValue(spots[indexes[turn] % len(spots)], COLORS[turn])
          
  rgbs.setValue(6).setValue(2).write()
    
  timestamp += duration
      
      
def countdown(timestamp):
  leds = [False] * 8
  sleepUntil(timestamp)
  rgbs.fill((1,1,1)).write()
  for counter in range(5, 0, -1):
    oleds.draw(DIGITS[counter], 8, 48, 0, mul=9).show()
    for c in range(8):
      timestamp += 1 / 8
      sleepUntil(timestamp)
      rgbs.setValue(c, (1,1,1) if leds[c] else (0,0,0)).write()
      leds[c] = not leds[c]
    
  oleds.fill(0).show()
  rgbs.fill((0,0,0)).write()
  
  return timestamp


def initHardware():
  global oleds, buzzers, lcds, rgbs

  ucuq.setDevice(DEVICES)
  rgbs = RGB(8, 20, 2)
  buzzers = ucuq.Buzzer(ucuq.PWM(5))
  oleds = ucuq.SSD1306_I2C(128, 64, ucuq.I2C(8, 9))
  lcds = ucuq.HD44780_I2C(16, 2, ucuq.SoftI2C(6, 7))
  
  for index, rgb in enumerate(rgbs):
    rgb.turn = index
    rgb.go = True

  ucuq.ntpSetTime()
    

def main():
  global timestamp
  
  initHardware()
  
  timestamp = countdown(time.time() + 2) + 1
  
  for rgb in rgbs:
    rgb.go = False
  
  gc.disable()
  
  oleds.contrast(0).draw(PICTURE, 64, 32).show()

  # ucuq.polyphonicPlay(JACQUES, 120, buzzers, callback)

  ucuq.polyphonicPlay(FUGUE, 160, buzzers, callback)
  
  gc.enable()

  rgbs.fill((0,0,0)).write()
  
  oleds.contrast(255)
  
  scroll("That's all Folks!", timestamp)
  
JACQUES = (
  "C44D44E44C44C44D44E44C44E44F44G45E44F44G45G43.A42G43F43E44C44G43.A42G43F43E44C44C44G34C45C44G34C45C44D44E44C44C44D44E44C44E44F44G45E44F44G45G43.A42G43F43E44C44G43.A42G43F43E44C44C44G34C45C44G34C45",
  "R6R6C44D44E44C44C44D44E44C44E44F44G45E44F44G45G43.A42G43F43E44C44G43.A42G43F43E44C44C44G34C45C44G34C45C44D44E44C44C44D44E44C44E44F44G45E44F44G45G43.A42G43F43E44C44G43.A42G43F43E44C44C44G34C45C44G34C45",
  "R6R6R6R6C44D44E44C44C44D44E44C44E44F44G45E44F44G45G43.A42G43F43E44C44G43.A42G43F43E44C44C44G34C45C44G34C45C44D44E44C44C44D44E44C44E44F44G45E44F44G45G43.A42G43F43E44C44G43.A42G43F43E44C44C44G34C45C44G34C45",
)

FUGUE = (
"R3A43G43A43F43A43E43A43D43A43C#43A43D43A43E43A43F43A43A33A43B33A43C#43A43D43A43C#43A43D43A43E43A43F44F#44G44C44Bb34A34Bb34C44D44F#34G34A34Bb34A34Bb34F#34G33G43G33G43D43G43D43G43C43Eb43C43Eb43C43Eb43C43Eb43C43F43C43F43C43F43C43F43Bb33D43Bb33D43Bb33D43Bb33D43Bb33E43Bb33E43Bb33E43Bb33E43A33C#43A33C#43A33C#43A33C#43F33D43F33D43F33D43F33D43E33Bb33E33Bb33E33Bb33E33Bb33D33A33D33A33D33A33D33A33E33G33E33G33E33G33E33G33F33..R1E33..R1D33..R1G33..R1F33..R1E33..R1F33..R1C#33..R1D33..R1C#33..R1D33..R1E33..R1F33..R1E33..R1F33..R1C#33..R1D35F35G35R5C35E35F35R5Bb25D35E35R5A25C#35D35R4F34Bb34Bb34A34A34G35R4A34Bb34Bb34A34A34G#35R6.R7R3D43C#43D43A33A33G33A33F#33D43C#43D43G33F43Eb43D43C#43E43A33C#43D33Eb43D43C43B33D43G33B33C33D43C43Bb33A33C43F#33A33D33C43Bb33A33Bb33A43G43F#43G43Bb33A33G33",
"R6R7R6R3D53C53D53Bb43D53A43D53G43D53F#43D53G43D53A43D53Bb43D53D43D53E43D53F#43D53G43D53F#43D53G43D53A43D53Bb44D53R3Bb43R3D53R3Eb54G43R3Eb53R3G43R3C54A43R3C53R3A43R3D54F43R3D53R3F43R3Bb44G43R3Bb43R3G43R3C#54E43R3C#53R3E43R3A44F43R3A43R3F43R3G44C#43R3G43R3C#43R3F44D43R3F43R3D43R3E44Bb33R3E43R3Bb33R3A33..R1A33..R1A33..R1A33..R1A33..R1A33..R1A33..R1A33..R1A33..R1A33..R1A33..R1A33..R1A33..R1A33..R1A33..R1A33..R1A35D45D45R5C45C45C45R5Bb35Bb35Bb35R5A35A35A35R4D44C#44C#44D44D44E45R4D44C#44C#44D44D44E45R5R3A43G43A43E43G43F43E43F45D45A33A43G43A43C#43G43F43E43F45E45D44A45G45.F#45F45Eb45.D44F#44C55Bb43A43Bb43Bb43",
"R6R7R7R7R7R7R7R7R7R6R3A53G53A53F53A53E53A53D53A53C#53A53D53A53E53A53F53A53A43A53B43A53C#53A53D53A53C#53A53D53A53E53A53F53A53E53A53D53A53C53A53Bb43A53C53A53D53G53Bb43G53E53G53D53G53C53G53Bb43G53A43G53Bb43G53C53F53A43F53D53F53C53F53Bb43F53A43F53G43F53A43F53Bb43E53G43E53C#53E53Bb43E53A43E53G43E53F43E53G43E53A43D53F43D53E43E53E43E53F43D53F43D53Bb43C#53Bb43C#53A43D53F43D53E43E53E43E53F43D53F43D53R3D53C#53D53B43D53C#53B43C#55R5R3D53C#53D53F53D53C#53B43C#55E55.D55C#54C55Bb45A45A45G45G45F#44A45Eb54D55R4G54",
)

DIGITS = (
  "708898A8C88870",
  "20602020202070",
  "708808304080f8",
  "f8081030088870",
  "10305090f81010",
  "f880f008088870",
  "708880f0888870",
  "f8081020404040",
  "70888870888870",
  "70888878088870",
)

unpack = lambda data: zlib.decompress(base64.b64decode(data)).decode()

PICTURE = unpack("eJytkmEOwyAIha8EtSvsPETvf4Q9EWz1z7Jkpm366ROeCJGPQuv4mXVj27hu3HRj23gVgJcI3FYB1hdB5xb/kqy3VZ7MnpjfYLtPxkrBF6VKnHWy72SaTDa3Dz7xHhtfD6ZvfGxcZjyyOEpZ1m1ejMUsa5arF6iGSS8WZk5P0C/D9VJ7Dm54vJiHKAJIr0X1KD0NfsuoTfGAvvzg2jjZwGxee0ub8CzzLrAXtzNZmvsJPftsDfN5YYMrvV6nhxh8d0/demMwrfxoNun5IOdoH1iCxbs/vJO5BxgK/0puxWgaRY7aowoXPdYh0Ew9BOEuM+LY7me6OmUcNy3q0s7Zcv8ZH/vm6ME=")

COLORS = (
  (10,0,0),
  (0,10,0),
  (0,0,10)
)

MAP = (
  (7,3),
  (0,4),
  (1,5)
)

main()

__import__("os")._exit(0)
