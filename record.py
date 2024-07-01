from datetime import datetime
import os
import json


def save(light, obj):
  obj['light'] = light
  obj['time'] = int(datetime.now().timestamp())
  with open(os.path.join(os.path.dirname(__file__), './data/' + light + '.json'), 'w+', encoding='utf-8') as f:
    json.dump(obj, f, ensure_ascii=False, indent=2)
  return obj


def get(light):
  with open(os.path.join(os.path.dirname(__file__), './data/' + light + '.json'), encoding='utf-8') as f:
    return json.load(f)
