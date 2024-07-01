LIGHT_HANA = {
  'wave': {
    'zero_high': 0.00025,
    'zero_low': 0.00075,
    'one_high': 0.00075,
    'one_low': 0.00025,
    'pause': 0.009,
  },
  'repeat': 4,
  'repeat_hold': 20,
  'code': {
    'a': '00110',  # Toggle Power
    'b': '10110',  # Cycle Color Temp
    'c': '01100',  # Brightness +
    'd': '10100',  # Brightness -
  },
  'prefix': '00111100110000110000',
}


def remote(button, repeat=0, hold=False):
  if button not in LIGHT_HANA['code']:
    print('Error: unrecognized button for Hana: ' + button)
    return 1
  elif repeat == 0:
    if hold:
      repeat = LIGHT_HANA['repeat_hold']
    else:
      repeat = LIGHT_HANA['repeat']
  code = LIGHT_HANA['prefix'] + LIGHT_HANA['code'][button]
  return (LIGHT_HANA['wave'], code, code, repeat)


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
    commands.append(('hana', 'a'))
  else:
    if not c_power and t_power:
      # turn light on first
      commands.append(('hana', 'a'))
    # adjust brightness
    if t_brightness > c_brightness:
      # if target is brighter
      # 10 => 100
      if c_brightness == 10 and t_brightness == 100:
        commands.append(('hana', 'c', 85))
      # 50 => 100
      elif c_brightness == 50 and t_brightness == 100:
        commands.append(('hana', 'c', 60))
      # 10 => 50
      elif c_brightness == 10 and t_brightness == 50:
        commands.append(('hana', 'c', 50))
    elif t_brightness < c_brightness:
      # if target is dimmer
      # 100 => 10
      if c_brightness == 100 and t_brightness == 10:
        commands.append(('hana', 'd', 85))
      # 100 => 50
      elif c_brightness == 100 and t_brightness == 50:
        commands.append(('hana', 'd', 55))
      # 50 => 10
      elif c_brightness == 50 and t_brightness == 10:
        commands.append(('hana', 'd', 60))

  return (_obj(t_power, t_brightness), commands)
