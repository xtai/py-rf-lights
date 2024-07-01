LIGHT_TAO = {
  'wave': {
    'zero_high': 0.00045,
    'zero_low': 0.00085,
    'one_high': 0.00105,
    'one_low': 0.00025,
    'pause': 0.008,
  },
  'repeat': 3,
  'repeat_hold': 16,
  'code': {
    'a': '000100100',  # Toggle Power
    'b': '001000010',  # Cycle Top Brightness
    'c': '000100110',  # Cycle Top Color Temp
    'd': '000110110',  # Cycle Down Brightness
    'e': '000100010',  # Cycle Down Color Temp
  },
  'prefix': '000000000001000100011100',
  'prefix_0': '00000000',
}


def remote(button, repeat=0, hold=False):
  if button not in LIGHT_TAO['code']:
    print('Error: unrecognized button for Tao: ' + button)
    return 1
  elif repeat == 0:
    if hold:
      repeat = LIGHT_TAO['repeat_hold']
    else:
      repeat = LIGHT_TAO['repeat']
  init_code = LIGHT_TAO['prefix'] + LIGHT_TAO['code'][button]
  code = LIGHT_TAO['prefix_0'] + init_code
  return (LIGHT_TAO['wave'], init_code, code, repeat)


def _obj(power, brightness, top_power, top_brightness, down_power, down_brightness):
  return {
    'power': bool(power),
    'brightness': int(brightness),
    'parts': [
      {
        'partName': 'top',
        'power': bool(top_power),
        'brightness': int(top_brightness),
      },
      {
        'partName': 'down',
        'power': bool(down_power),
        'brightness': int(down_brightness),
      },
    ]
  }


def _part(obj, attribute):
  parts = {part['partName']: part[attribute] for part in obj['parts']}
  return parts.get('top', ''), parts.get('down', '')


def sync():
  return _obj(True, 100, True, 100, True, 100)


def _calc_power(current, target_part, target_power):
  # calculate target power state
  t_top, t_down = _part(current, 'power')

  if target_part == 'default':
    t_top, t_down = target_power, target_power
  elif target_part == 'top':
    t_top = target_power
  elif target_part == 'down':
    t_down = target_power

  return {
    'default': bool(t_top or t_down),
    'top': bool(t_top),
    'down': bool(t_down),
  }


def _calc_brightness(current, target_part, target_brightness):
  # calculate target brightness state
  t_top, t_down = _part(current, 'brightness')

  if target_brightness > 0:
    # target_brightness should > 0
    # allowed birghtness [25, 50, 75, 100]
    if target_brightness <= 40:
      target_brightness = 25
    elif target_brightness > 40 and target_brightness <= 70:
      target_brightness = 50
    elif target_brightness > 70 and target_brightness <= 90:
      target_brightness = 75
    elif target_brightness > 90:
      target_brightness = 100

    if target_part == 'default':
      # change default birghtness should apply to both lights
      t_top, t_down = target_brightness, target_brightness
    elif target_part == 'top':
      # change top birghtness
      t_top = target_brightness
    elif target_part == 'down':
      # change down birghtness
      t_down = target_brightness

  return {
    'default': int(t_top),
    'top': int(t_top),
    'down': int(t_down),
  }


def _commands_birghtness(c_top, c_down, t_top, t_down):
  # calculate commands for the target brightness state
  # each click cycle the brightness [25, 50, 75, 100] sequentially
  top_clicks = int((t_top - c_top) / 25) % 4
  down_clicks = int((t_down - c_down) / 25) % 4
  return [('tao', 'b')] * top_clicks + [('tao', 'd')] * down_clicks


def _commands_power(c_top, c_down, t_top, t_down):
  # calculate commands for the target power state
  # State 1 - top: on, down: on
  # State 2 - top: on, down: off
  # State 3 - top: off, down: on
  # State 4 - top: off, down: off
  if (c_top or c_down) and (not t_top and not t_down):
    # [1,2,3 => 4] if either lights is on, turn all lights off
    return [('tao', 'a')]
  elif (c_top and c_down) and (t_top and not t_down):
    # [1 => 2] both lights are on, turn down light off
    return [('tao', 'd', LIGHT_TAO['repeat_hold'])]
  elif (c_top and c_down) and (not t_top and t_down):
    # [1 => 3] both lights are on, turn top light off
    return [('tao', 'b', LIGHT_TAO['repeat_hold'])]
  elif (c_top and not c_down) and (t_top and t_down):
    # [2 => 1] only down light is off, turn top light on
    return [('tao', 'd', LIGHT_TAO['repeat_hold'])]
  elif (not c_top and c_down) and (t_top and t_down):
    # [3 => 1] only top light is off, turn down light on
    return [('tao', 'b', LIGHT_TAO['repeat_hold'])]
  elif (not c_top and not c_down) and (t_top and t_down):
    # [4 => 1] both lights are off, turn all lights on
    return [('tao', 'a')]
  elif (not c_top and not c_down) and (t_top and not t_down):
    # [4 => 2] both lights are off, only turn top light on
    return [('tao', 'b', LIGHT_TAO['repeat_hold'])]
  elif (not c_top and not c_down) and (not t_top and t_down):
    # [4 => 3] both lights are off, only turn down light on
    return [('tao', 'd', LIGHT_TAO['repeat_hold'])]
  return []


def clicks(current, target):
  power, brightness, part = target

  # reject illegal parts
  if part not in ['default', 'top', 'down']:
    return (current, [])

  if brightness == 0:
    power = False

  # calculate target power and brightness state based on input and current state
  target_power = _calc_power(current, part, power)
  target_brightness = _calc_brightness(current, part, brightness)

  commands = []

  # get a list of commands to the target power and brightness state
  commands.extend(_commands_power(*_part(current, 'power'),
                                  target_power['top'],
                                  target_power['down']))
  commands.extend(_commands_birghtness(*_part(current, 'brightness'),
                                       target_brightness['top'],
                                       target_brightness['down']))

  # compensate main brightness reading for only when down light is on
  if not target_power['top'] and target_power['down']:
    target_brightness['default'] = int(target_brightness['down'] / 5)

  return (_obj(target_power['default'],
               target_brightness['default'],
               target_power['top'],
               target_brightness['top'],
               target_power['down'],
               target_brightness['down']), commands)
