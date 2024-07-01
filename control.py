#!/usr/bin/env python3

import argparse
import json
import sys

import remote
import record

lights = ['tao', 'tx', 'hana']
modules = {}

for l in lights:
  try:
    modules[l] = __import__('light.' + l, fromlist=[None])
  except ImportError:
    print('Error importing ' + l)


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Control stateful lights')
  parser.add_argument('--light', help='tao, tx, or hana')
  parser.add_argument(
      '--part', help='default, tao: top, down', default='default')
  parser.add_argument('--on', action='store_true')
  parser.set_defaults(power=True)

  parser.add_argument('--off', dest='power', action='store_false')
  parser.add_argument('--brightness', type=int, default=-1)
  parser.add_argument('--sync', action='store_true')
  parser.add_argument('--status', action='store_true')

  args = parser.parse_args()

  if args.light in lights:
    if args.status:
      sys.stdout.write(json.dumps(record.get(args.light)))
    elif args.sync:
      sys.stdout.write(json.dumps(record.save(
          args.light, modules[args.light].sync())))
    else:
      current = record.get(args.light)
      target = (args.power, args.brightness, args.part)
      final, clicks = modules[args.light].clicks(current, target)
      for c in clicks:
        remote.click(*c)
      sys.stdout.write(json.dumps(record.save(args.light, final)))
  else:
    print('Light is what? ' + str(args.light))
