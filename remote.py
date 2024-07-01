#!/usr/bin/env python3
import argparse
import time
import sys
import atexit
import RPi.GPIO as GPIO

lights = ['tao', 'tx', 'hana']
modules = {}

for l in lights:
  try:
    modules[l] = __import__('light.' + l, fromlist=[None])
  except ImportError:
    print('Error importing ' + l)

TRANSMIT_PIN = 17
CLICK_PAUSE = 0.25


def transmit(wave, init_code, code, repeat):
  GPIO.setmode(GPIO.BCM)
  GPIO.setwarnings(False)
  GPIO.setup(TRANSMIT_PIN, GPIO.OUT)
  try:
    transmit_code(wave, init_code)
    for _ in range(repeat):
      transmit_code(wave, code)
  finally:
    GPIO.cleanup()
    time.sleep(CLICK_PAUSE)


def transmit_code(wave, code):
  for c in code:
    if c == '0':
      GPIO.output(TRANSMIT_PIN, GPIO.HIGH)
      time.sleep(wave['zero_high'])
      GPIO.output(TRANSMIT_PIN, GPIO.LOW)
      time.sleep(wave['zero_low'])
    elif c == '1':
      GPIO.output(TRANSMIT_PIN, GPIO.HIGH)
      time.sleep(wave['one_high'])
      GPIO.output(TRANSMIT_PIN, GPIO.LOW)
      time.sleep(wave['one_low'])
  GPIO.output(TRANSMIT_PIN, GPIO.LOW)
  time.sleep(wave['pause'])


def click(light, button, repeat=0, hold=False):
  transmit(*modules[light].remote(button, repeat, hold))


def exithandler():
  GPIO.cleanup()
  sys.exit(0)


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Remote control of stateless rf lights')
  parser.add_argument('--gpio', type=int, default=17)
  parser.add_argument('--light', help='tao, tx, or hana')
  parser.add_argument('--button', help='Button ID: tao: a-e, tx: a-k, x, hana: a-d')
  parser.add_argument('--hold', action='store_true', default=False, help='Apply default the hold for a button.')
  parser.add_argument('--repeat', type=int, default=0, help='Repeat a command.')
  args = parser.parse_args()
  click(args.light, args.button, args.repeat, args.hold)
  atexit.register(exithandler)
