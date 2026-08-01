import base64
import zlib

import shared
import show
import ucuq


from show import indexes as indexes_, sleepUntil as sleepUntil_
from fractions import Fraction


def decompressVoiceString(compressed_b64):
    compressed = base64.b64decode(compressed_b64)
    return zlib.decompress(compressed).decode("utf-8")

def parseVoice(marked_str):
    marker, payload = marked_str[0], marked_str[1:]
    if marker == "C":
        voice_str = decompressVoiceString(payload)
    elif marker == "R":
        voice_str = payload
    else:
        raise ValueError(f"Marqueur de voix inconnu : {marker!r}")

    notes = []
    for token in voice_str.split(","):
        pitch_str, duration_str = token.split(":")
        notes.append([int(pitch_str), Fraction(duration_str)])
    return notes


def scroll_(text, start, devices):
  width = len(devices.lcds) * 16
  resizedText = " " * width + text + " " * width
  prevSubText = [None] *  len(devices.lcds)
  devices.lcds.clear()
  
  for s in range(138):
    i = (len(resizedText) - width + 1) * s // 137
    sleepUntil_(start)
    for lcd in range(len(devices.lcds)):
      subText = resizedText[i + lcd * 16:i + (lcd + 1) * 16]
      if prevSubText[lcd] != subText:
        prevSubText[lcd] = subText
        devices.lcds[lcd].moveTo(0,0).putString(subText)
      if not all(c == ' ' for c in subText):
        devices.lcds[lcd].backlightOn()
#        devices.oleds[lcd].scroll(0, 1).hline(0,0,64, 0).show()
      else:
        devices.lcds[lcd].backlightOff()
    start += .07


def callback_(note, turn, prev, devices):
  buzzer = devices.buzzers[turn]
  
  if note != 0 and prev[turn] == note:
    buzzer.off()
#    devices.oleds[turn].contrast(0)
    ucuq.getDevice()[turn].sleep(0.015)
  else:
    prev[turn] = note

  if note > 0:
    devices.rings[turn].go = True
#    devices.oleds[turn].contrast(1)
    devices.lcds[turn].backlightOn()
    indexes_[turn] += 1
  elif note == 0:
    pass
#    devices.oleds[turn].contrast(0)

  buzzer.play(note)

  spots = MAP_[turn]
  
  for spot in spots:
    devices.rings.setValue(spot, (0,0,0))
    if note != 0:
      devices.rings.setValue(spots[indexes_[turn] % len(spots)], COLORS_[turn])
          

def updateRings(devices):
  devices.rings.setValue(5).setValue(6).write()
  
  # show.displayRingGauges(devices)

def getMusicEvents(voice, turn, prev, devices ):
  events = []

  duration = 0

  for note in parseVoice(voice):
    events.append((lambda note = note, turn = turn: callback_(note[0], turn, prev, devices), note[1]))
    duration += note[1]

  return events, duration

def set(dom):
  html = ""
  for part in PARTS_:
    html += f'<option value="{PARTS_.index(part)}">{part[0][0]}</option>'

  dom.inner("ShowTrios", html)

def oledCallback(oleds, notes, minNotes, maxNotes):
  oleds.scroll(dx=0, dy=1)
  oleds.hline(0,0,128, 0)
  for note in notes:
    minNote = minNotes[notes.index(note)]
    maxNote = maxNotes[notes.index(note)]
    if note:
      oleds.pixel(128 // 3 * notes.index(note) + 128 // 3 - 128  // 3 * (note - minNote) // (maxNote - minNote), 0)
    for oled in oleds:
      oled.hline(128 // 3 * oleds.index(oled), 63, 128 // 3, 1)
  oleds.show()


def getOLEDEvents(part, oleds):
  minNotes = [100] * 3
  maxNotes = [0] * 3
  minDelay = 100

  events = []
  voices =[]

  for voice in part:
    for note in parseVoice(voice):
      minNotes[part.index(voice)] = min(minNotes[part.index(voice)], note[0] if note[0] else minNotes[part.index(voice)])
      maxNotes[part.index(voice)] = max(maxNotes[part.index(voice)], note[0])
      minDelay = min(minDelay, note[1] if note[1] else minDelay)

  print(float(minDelay))

#  minDelay = max(minDelay, 1/3)

  for voice in part:
    voices.append(parseVoice(voice))

  while len(voices[0]) and len(voices[1]) and len(voices[2]):
    notes = (voices[0][0][0], voices[1][0][0], voices[2][0][0])
    events.append((lambda notes = notes: oledCallback(oleds, notes, minNotes, maxNotes), minDelay))
    for voice in voices:
      voice[0][1] -= minDelay
      while len(voice) and voice[0][1] <= 0:
        if len(voice) > 2:
          voice[1][1] -= voice[0][1]
        del voice[0]

  return events

COMMIT_DELAY_ = 2

def getCommitEvents_(duration):
  events = []
  elapsed = 0

  while elapsed <= duration:
    events.append((lambda: ucuq.commit(), COMMIT_DELAY_))
    elapsed += COMMIT_DELAY_

  return events

LCD_TITLE_DELAY_ = 1/3

def getLCDTitleEvents(title, duration, lcds):
  title = " " * 16 + title + " " * 16
  counter = 0
  events = []

  while duration > 0:
    events.append((lambda text = title[counter % (len(title) - 16):][:16]: lcds.moveTo(0,0).putString(text), LCD_TITLE_DELAY_))
    duration -= LCD_TITLE_DELAY_
    counter += 1

  return events


def launch(part, timestamp, devices):
  devices.lcds.uploadUpwardGaugeChars()

#  devices.oleds.contrast(0).draw(PICTURE_, 64, 32).show()
    
  for index, ring in enumerate(devices.rings):
    ring.turn = index
    ring.go = False 

  timestamp = timestamp + 1
  prev = [None] * len(devices.buzzers)

  sleepUntil_(timestamp)
  
  eventList = []

  maxDuration = 0

  eventList.append(getOLEDEvents(PARTS_[part][1], devices.oleds))

  for voice in PARTS_[part][1]:
    events, duration = getMusicEvents(voice, PARTS_[part][1].index(voice), prev, devices)
    eventList.append(events)
    maxDuration = max(maxDuration, duration)

  eventList.append(getCommitEvents_(maxDuration))

  eventList.append(getLCDTitleEvents(PARTS_[part][0][1], duration, devices.lcds))

  cb = ucuq.setCommitBehavior(ucuq.CB_MANUAL)

  timestamp += ucuq.playEvents(
    eventList,
    lambda
      _,
      cumul:
        (
          updateRings(devices),
          sleepUntil_(timestamp + cumul),
        )
  )
  
  ucuq.setCommitBehavior(cb)

  devices.rings.fill((0,0,0)).write()
  
  devices.oleds.contrast(255)
  
  return scroll_("That's all Folks!", timestamp, devices)


PARTS_ =  (
  (
    (
    "Titelouze",
    "Ave Maris Stella"),
    (
      'CeNqFUlsWhCAI3VDnTApSuv+FjQKKmM38ZAjcB0i5hOMK7RNL+ET+rwfxPdZ/lAyuUSigde24RpfktBIs0krLKSYsmBrdwlcPkj7aiVglTUTGB07SWokiniPvCCZjlf04BRD7sBxqz3phNFokB37CE0GSQyopWoSSE5mNpQPw1h4WxvL6VXIFGilwHBFnVvpGRuaNBWwQdkK9pecgpqe2eSbO0MYJC3ozlS2fd2X/+pMZjm5FqONoRQKQ8o/BgENInuH12d19qdunYTtjSiqxSj2/ix/AHw==',
      'CeNqNUlsOwyAMuxAS4RFYuf/BViclhK6V9hMTTB62YBo5cEc4EHhLG9iWR5IQswGNHisgnTCfFmXw4LxKQY+to5zlZasKvNiL6AqHlSgnLett9BwQZVUBXllVTrfDFGtQpw7b3KlyYtImTeBqzJYF/iBs4zGLnTTJtwb0suYSJPveXUjOBXiyjHxTM436MeNNmlhAD03/rBc7yLvRllgzrjgXnu0JnPH5CoKcaOCevsQXhuo=',
      'CeNptUVsSwDAEvFBnitA0uf/BSshz+rNssV0CFa+HDNhAKt7Ucgvte9acvcIn45qizwKMKa9FZ1oYTf1VMx2awV7/n4bic+XPxGnJAvhGaTOCh5HW5mRZQ3JVkNqzCWBAo5oGBacYEC0YkBfYVHYBfp1iQAiYM5F+YFG74gtLHONvhwfjWeezSOnbtWHpU6RHgA+it2cq',
    )
  ),
  (
    (
      "Ano. Loeb Gott",
      "Anonymous (18th) - Lobt Gott, ihr Christen, allzugleich"
    ),(
      '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',
    )
  ),(
    (
      "BWV 528b",
      "J.S. BACH - Sonate en trio pour orgue n°4 - (BWV 528) - Andante"
    ),(
      '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'
    )
  ),
  (
    (
      "BWV 870a",
      "J.S. BACH - Prélude et fugue en mi majeur (BWV 870) - Fugue"
    ),
    (
      'CeNrlVVuywyAI3VBmalCC6f4XdkVARU3n9rs/NbyOejzQ8D5fcFxUlnRcKAuJM8hyv8/qOtTWpLSULE5w1rbg/oACu7rtDuoMdcF7tCzFWT4F6UOdQl/tgO27R9h/u8NFjyDfoPXoru6JAE4QosMbDhIMOmXpKGUhBmaXhMVhWUkseT6O8TFbhTosK4kFR25A+Jo3N6CTT7ieHVQeNU7RcJgIkuwscFnvIk6ivn8/TRwuGEfwIb7ckLmt1wxPbPR9vPN01raAnlAemNSYEQrupKkx9fRqFtOC4N59Bfvmmvp2o6Rmy6eM2y51Ch025V7ZmjJZ8xTARxmjLP8eDaWbY2/q0uJx6PSSUn8KIgo+Ss9iagm86LRgGYNAaWabjhUYrL/rpi3TBij0o//6qA3fTdo2bsHRQsNI2PMJE58mn93cupIfbE3wa7+4Hqwi5nD11teKbdrjyiO4oZGcKKDJgIQYVH70x1EUTIeVy9gVC0fKpkoRuOVGp2cZqdhxpDFm4WJ2f4/ZSRW7VIf/tRbOI1uThY52GOc7jHQE25A/wx+067kA',
      'CeNrNVd3WhCAIfKHOWULU1vd/sC/FftgmqrMX+91kgzCIjkhlzC8eMpfxJUMedaiIh5TbkFMZhyzzhxQffaXNH4zpbVxgQDpn6eEx6hA2xINMbYjzEpupr21x4kPIwUgGwYDssBCKgxn4OtH1OuWNOAXFWaOgih7X11mSiYNGi94IRcTi1YDCE+2NHSUG6OASqrZV4l1NSTOkTp338vswSuH6qf+7LF15Ksg6qByp8KRSnU9QCbpwpbtz1S+t+gW+mwSMUaJBKKBvJmRZ0ORIFbJ48v8P9wxXZKqVZHZQWUR7jpBBASHjEuxx5NvbGktaKqcSF52y6nQV0qIu2lQz07NZT3TkkS9VckdkclnjDWp4opglPhT1l2J5cGpe+4ZagxWFh/t5/7IfRHZ+wbym7F3oK8+tF2pzbU8Caw387Wu+XoXmVk0/e5FvNJrsNJpw2YR6awkJNGCBcxHMLQ2KnOzZ4SRnLpzL0q3dq4/Oq7X5bLXR2YmPlY39bd69wwrmldRf+gNWkDGx',
      'CeNqtVVmWAyEIvFDeiwsu7f0PNgqKYmiTmclPbKAKEIGY4v3TPZIt9gmP5OgQUrw2pV+UhqTESMI5JPefqWhHJxIDJbZl2+DoJLNioICkCgay+YpDRjasGCggqYIj2aAEOhjpOHicAWdwICo0yc8cFk498MIUfZQg0JHW0kmlEQgNn8zBCWg8KUlIf0UjJNAkAQnXgUeliXk++/ieFk48K220SfKmUYuVNOkDyPX2QfRihEMt4f8v8puO+XOCvTVPeX6zV0JSOmeTdkjbPi+uvaB7EaERAk1hp6NP9LLagFxzCTgQVZ4q7ZbtlPC7j7OyCfuLjYUBJyzQlrpbpSdCvPPiWFpsbuTAOY09G1+8Or5zuz8zumKJnURlcCUOxgCjHr8xFG/lEd2KgrlCqnOXp7XWW+HC+0H43mzyjj4MwAcjoqUwO9fKRrZLe8Ldfpg2XLmzBZVY7G7xLee2hg/CqZDk37b0BYouiIeH0gzmB4V7qmg=',
    )
  ),
  (
    (
      "BWV 847b",
      "J.S. BACH - Prélude et fugue en ut mineur (BWV 847) - Fugue"
    ),(
    'CeNrNV+2OxCAIfKFLThT82Pd/sL1c0t2kI3W0bu76k8AAyjg0PEptWtJ3DL/fV4mHRQ+LgCWeo3IBS92DXHScaxuynaPeuRT6Et8HcZJfz8vSwFJ9n+j3ZWBZQq4yPrFdyDkTE9Vmoo7bCXAVaInj6yJHI6ZcVdp+aDzngMlWqx77EAOd4z1aih8V7tX8qqcQVAGfQLCASSUEc3Upau3duOhC3NYz0SjcxDtK3Sgkdwm+5ZIW7qNOPBIzetaxlHFyLNDgUM0IH8SBWbG0EpXRpy7VbEQ9QlRYN51YXqrwYnwUdEj9ScAZS5uQCersQp4TT/F9AAdvOTBqqjN9zampbhNq1DxIlu9Bxxnp9iVO3FRX5bgwKPedHmQM8/9/SZDKkfCxv/gB+dyPnq+mnxN35pjTzJvlq875zaKW+7DiArg25lpnmJK/4SmMsrq7LDO4naXPiKXP3zin2mL2eh3u9WuUtUYofSQsxDZJEKvDfOYXFOUP+9IT0X/KCU+QsaTM',
    'CeNrFV9FuwzAI/KFJNfZhk/7/h22q1lTbBRtbaZNHRA44DkLSXQqyJMgtp8fz1eTebEMrN/xa6kaWRhYlSyFLJkt6WvboShaQJZOFcF45+z4HOJThKzooQ/F9GKdTaSRWJuZ3ixFy83FAPlOMbT4OyIcV1WEeoZxzqQbZpkhM9JZ1CuvITsfUH7RHZ3w6w8M42UeWvfaVXrB6xVd4RJl+Oh0h+C8FWrM2XaEdsYZM7KR3Ab9o5+XD7RPXh3EO1n4JfAjaGLmXIWZWBE7C6ay1p8VoKCxfykYNVKEfZIO0YTS4Bz4yjrVYVz7n2DjYu0vHRq2BFbqtvDU3BbSQxBdUR3Q+jAWUakOY0D1Z/sMotVjrOZ9fJdq1cw5EFsKOw01P59zbpEolVSpRCDoZCiVYbPh5AwkOgVA9H1A6mMEhWSqxrDL2YRyQvEFzg+LnDNITSLsgfYMaeHoVdiUb3OWL2cAKY+9jo9gH2aC9BvWroEPe3Do1EGltbssSO/UKTvMM7xbYdDgHWdPKVl1ElsBU0K/i3OS4P5gqgQRtfGowPaX+Df4TO30D4XXlhQ==',
    'CeNrFV9luAzEI/KFK8cFh7/9/WNWq3Ug7BmNvouQR4QFmODbpqE0aZdVHSb+/L0mHtk5aH/Rn4X61PH3+XzGDRa6WPWQp81gvQ66Aw2A568q2D+JkOx87Z9ZAPoFYDLGozX32cEjAQmCBnAljNZv597MxqKJ9ko3a38UG9XtVFHsntPlOGOyNOsfBWMkOFRnlleCvKuIpRYGGKiCFjSx5R4qBT93JEH1OF7ZqIGCQeC7oHl2OT2TWHRxHYmd/tx1KB7eiBW5yCTRPmd+lwZ0kewTyVUBnzcFEkm4eqlJ/PmO6By0vuoEVg+k9aLPnI7pHFh0C4z5QsPDcR6F9FAhTaB/F9unz/TRoQ+dVNkunQKHAoMDVFl5J2U7HYdl+BC4CfaHJFiIiFpnIArPuMZhBdCefrcYAzQe9XOaPnJE480ML2zWs8C74f0Xng7Q5xnUHJ62EIghljw1KvCS67aLZXldLKUdu5L3Fk+8s6kArI6Npx4Uvn3bpSN9jZz4Y',
    )
  ),
  (
    (
      "BWV 848b",
      "Johann Sebastian Bach - Prelude and Fugue in C-sharp major (BWV 848) - Fugue"
    ),
    (
      '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'
    )
  )
)

PICTURE_ = shared.unpack("eJytkmEOwyAIha8EtSvsPETvf4Q9EWz1z7Jkpm366ROeCJGPQuv4mXVj27hu3HRj23gVgJcI3FYB1hdB5xb/kqy3VZ7MnpjfYLtPxkrBF6VKnHWy72SaTDa3Dz7xHhtfD6ZvfGxcZjyyOEpZ1m1ejMUsa5arF6iGSS8WZk5P0C/D9VJ7Dm54vJiHKAJIr0X1KD0NfsuoTfGAvvzg2jjZwGxee0ub8CzzLrAXtzNZmvsJPftsDfN5YYMrvV6nhxh8d0/demMwrfxoNun5IOdoH1iCxbs/vJO5BxgK/0puxWgaRY7aowoXPdYh0Ew9BOEuM+LY7me6OmUcNy3q0s7Zcv8ZH/vm6ME=")

COLORS_ = (
  (10,0,0),
  (0,10,0),
  (0,0,10)
)

MAP_ = (
  (0,7),
  (1,2),
  (3,4)
)
