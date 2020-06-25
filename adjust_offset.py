#!/usr/bin/env python3

import mbrush
import numpy as np

img = np.ones([360,32,3], dtype=np.uint8)*255

data = bytes()

#img[0:120:2,16,0] = 0
#img[120:240:2,16,1] = 0
#img[240:360:2,16,2] = 0

#for i in range(32,40):
#  color_offsets = [
#    i*2, i*2+8, i+8, i, 0, 8
#  ]
#  _data = mbrush.convert_to_mbd(img, color_offsets)
#  if data:
#    data += _data[16:]
#  else:
#    data = _data

img[0:60:2,16,0] = 0
img[61:120:2,16,0] = 0
img[120:180:2,16,1] = 0
img[181:240:2,16,1] = 0
img[240:300:2,16,2] = 0
img[301:360:2,16,2] = 0

for i in range(4,12):
  color_offsets = [
    72, 72+i, 36+i, 36, 0, i
  ]
  _data = mbrush.convert_to_mbd(img, color_offsets)
  if data:
    data += _data[16:]
  else:
    data = _data

mbrush.upload(data)
