import copy
import random
import types

import ucuq

import show


from show import sleepUntil as sleepUntil_

MAX_ = ucuq.ravel.SERVO_MAX
STEP_ = 50
LCD_DELAY_ = .4
SERVO_MUL_ = 11
SERVO_DELAY_ = LCD_DELAY_ / SERVO_MUL_
REMAINDER_ = ucuq.ravel.LCD_WIDTH * 3
AMOUNT_ = REMAINDER_ * SERVO_MUL_
CYCLES_ = 100

class Level_:
  def __init__(self, rest):
    self.rest = rest

    if rest == 0:
      self.up = random.randrange(0, MAX_ + 1)
      self.down = 0
      self.step = STEP_
    else:
      self.up = rest
      self.down = random.randrange(0, rest)
      self.step = -STEP_

    self.value = rest

  def update(self):
    self.value = max(min(self.value + self.step, MAX_), 0)
    if self.step > 0 and self.value >= self.up:
      self.step = -STEP_
      self.up = random.randrange(self.down + 1, MAX_ + 1)
    elif self.step < 0 and self.value <= self.down:
      self.step = STEP_
      self.down = random.randrange(0, self.up)

    return self

  def ending(self):
    if self.rest == 0:
      if self.value > 0:
        self.value = max(self.value - STEP_, 0)
    else:
      if self.value < self.rest:
        self.value = min(self.value + STEP_, MAX_)

    return self

  def nothing(self):
    return self


def handleLevels_(levels, method):
  levels.append(method(copy.copy(levels[-1])))
  levels.pop(0)


def getLevelEvents__(tracking):
  for i in range(CYCLES_ * SERVO_MUL_):
    handleLevels_(tracking.tops, Level_.update)
    handleLevels_(tracking.bottoms, Level_.update)

    yield SERVO_DELAY_

  while (tracking.tops[-1].value != 0 or tracking.bottoms[-1].value != MAX_):
    handleLevels_(tracking.tops, Level_.ending)
    handleLevels_(tracking.bottoms, Level_.ending)

    yield SERVO_DELAY_

  for _ in range(REMAINDER_ * SERVO_MUL_):
    handleLevels_(tracking.tops, Level_.nothing)
    handleLevels_(tracking.bottoms, Level_.nothing)

    yield SERVO_DELAY_

  tracking.stop = True


def getServoEvents__(levels, index, servo):
  while (True):
    if levels[index].value != levels[index+1].value:
      servo.setSmooth(MAX_ - levels[index].value)

    yield SERVO_DELAY_


def getLevelChar_(level, up):
  level = 7 * level // MAX_

  if up:
    if level == 0:
      return " "
    else:
      return chr(level - 1)
  else:
    if level == 7:
      return " "
    else:
      return chr(level)


def getLCDEvents_(tracking, lcds):
  while (True):
    topGauges = ""
    bottomGauges = ""
    for x in range(ucuq.ravel.LCD_WIDTH * 3):
      topGauges += getLevelChar_(tracking.tops[(x + 1) * SERVO_MUL_ - 1].value, True)
      bottomGauges += getLevelChar_(tracking.bottoms[(x + 1) * SERVO_MUL_ - 1].value, False)

    lcds.moveTo(0,0).putString(topGauges)
    lcds.moveTo(0,1).putString(bottomGauges)

    yield LCD_DELAY_


def sleepCallback_(tracking, user, timestamp):
  sleepUntil_(timestamp + tracking.cumul, 1/3)

  return not user.tracking.stop


def launch(timestamp, devices):
  tracking = types.SimpleNamespace(tops = [Level_(0) for _ in range(AMOUNT_)], bottoms = [Level_(MAX_) for _ in range(AMOUNT_)], stop = False)

  timestamp += 1
  sleepUntil_(timestamp, 0)

  uppers = devices.uppers
  lowers = devices.lowers
  lcds = ucuq.LCD_Strip(devices.lcds.uploadVPeakChars().backlightOn())

  cb = ucuq.setCommitBehavior(ucuq.CB_MANUAL)

  ucuq.dispatchEvents(
    (
      getLevelEvents__(tracking),
      *(
        events for i in range(3) for events in (
          getServoEvents__(tracking.tops, i * AMOUNT_ // 3, uppers[i]),
          getServoEvents__(tracking.bottoms,  i * AMOUNT_ // 3, lowers[i]),
        )
      ),
      getLCDEvents_(tracking, lcds),
    ),
    lambda tracking, user: sleepCallback_(tracking, user, timestamp),
    tracking = tracking,
    timestamp = 0
  )

  ucuq.setCommitBehavior(cb)

  uppers.park()
  lowers.park()
  lcds.backlightOff()
