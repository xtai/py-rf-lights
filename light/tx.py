LIGHT_TX = {
  'wave': {
    'zero_high': 0.00030,
    'zero_low': 0.00134,
    'one_high': 0.00134,
    'one_low': 0.00030,
    'pause': 0.009,
  },
  'repeat': 3,
  'repeat_power': 5,
  'repeat_hold': 20,
  'code': {
    'a': '000010010',  # Power On
    'b': '000010110',  # Power Off
    'c': '000011010',  # Brightness +
    'd': '000000110',  # Brightness -
    'e': '000110000',  # Bright Warm
    'f': '000000010',  # Warmer
    'g': '000011110',  # Cooler
    'h': '000001010',  # Half Neutral
    'i': '000001110',  # Dim Cycle
    'j': '000001100',  # Bright Neutral
    'k': '000110100',  # Bright Cool
    'x': '000000000',  # Paring
  },
  'prefix': '0001000111110011',
}


def remote(button, repeat=0, hold=False):
  if button not in LIGHT_TX['code']:
    print('Error: unrecognized button for Tx: ' + button)
    return 1
  elif repeat == 0:
    if hold:
      repeat = LIGHT_TX['repeat_hold']
    elif button == 'a' or button == 'b':
      repeat = LIGHT_TX['repeat_power']
    else:
      repeat = LIGHT_TX['repeat']
  code = LIGHT_TX['prefix'] + LIGHT_TX['code'][button]
  return (LIGHT_TX['wave'], code, code, repeat)


def _obj(power, brightness):
  return {
    'power': bool(power),
    'brightness': int(brightness),
  }


def sync():
  return _obj(True, 100)


def clicks(current, target):
  c_power, c_brightness = current['power'], current['brightness']
  t_power, t_brightness, part = target

  # Allowed targeted brightness: [10, 50, 100]
  if t_brightness <= -1:
    # power command only
    t_brightness = c_brightness
  elif t_brightness == 0:
    t_power = False
    t_brightness = c_brightness
  elif t_brightness > 0 and t_brightness <= 25:
    t_brightness = 10
  elif t_brightness > 25 and t_brightness <= 75:
    t_brightness = 50
  elif t_brightness > 75:
    t_brightness = 100

  commands = []
  if c_power and not t_power:
    # turn light off, ignore target brightness
    commands.append(('tx', 'b'))
  else:
    if not c_power and t_power:
      # turn light on first
      commands.append(('tx', 'a'))
    # adjust brightness
    if t_brightness > c_brightness:
      # if target is brighter
      # any => 100
      if t_brightness == 100:
        commands.append(('tx', 'e'))
      # 10 => 50
      elif c_brightness == 10 and t_brightness == 50:
        commands.append(('tx', 'c', 10))
    elif t_brightness < c_brightness:
      # if target is dimmer
      # 100 => 10
      if c_brightness == 100 and t_brightness == 10:
        commands.append(('tx', 'd', 30))
      # 100 => 50
      elif c_brightness == 100 and t_brightness == 50:
        commands.append(('tx', 'd', 15))
      # 50 => 10
      elif c_brightness == 50 and t_brightness == 10:
        commands.append(('tx', 'd', 15))

  return (_obj(t_power, t_brightness), commands)
