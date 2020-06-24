from .mbd import convert_to_mbd
from .api import upload

def print_rgb(img, host='192.168.44.1'):
  data = convert_to_mbd(img)
  upload(data)
