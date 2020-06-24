#!/usr/bin/env python3

import numpy as np

LINE_WIDTH = 180
COLOR_INTERVAL = 32

def _dither(img):
  assert(len(img.shape) in [2,3])
  assert(img.dtype == np.uint8)

  img = np.float32(img)/255.
  if len(img.shape) == 2:
    img = np.pad(img, [[0,1], [1,1]])
  else:
    img = np.pad(img, [[0,1],[1,1],[0,0]])
  
  for y in range(0, img.shape[0]-1):
    for x in range(1, img.shape[1]-1):
      oldpixel = img[y,x].copy()
      newpixel = np.float32(oldpixel >= .5)
      img[y,x] = newpixel
      error = oldpixel - newpixel
      img[y, x+1] += 7/16 * error
      img[y+1, x-1] += 3/16 * error
      img[y+1, x] += 5/16 * error
      img[y+1, x+1] += 1/16 * error
  img = np.uint8(img[0:-1,1:-1])
  return img

def _add_line(buf, line, channel):
  """
  buf: np.ndarray
    Output line buffer with shape [18,120] and dtype np.uint8,
    each element of which is either 0 or 1.
  line: np.ndarray
    Binary image column from bottom to top
    with shape [180] and dtype np.uint8,
    each element of which is either 0 or 1.
  channel: str
    'C0', 'C1', 'M0', 'M1', 'Y0', or 'Y1'.
  """
  
  assert(buf.dtype == np.uint8)
  assert(buf.shape == (18,120))
  assert(np.all(buf <= 1))
  assert(line.dtype == np.uint8)
  assert(line.shape == (180,))
  assert(np.all(line <= 1))
  
  line = line.reshape(20,9)
  inds = np.array([0,10,1,11,2,12,3,13,4,14])
  inds += {
    'Y0': 0,
    'Y1': 5,
    'M0': 20,
    'M1': 25,
    'C0': 40,
    'C1': 45
  }[channel]
  inds = np.concatenate([inds, inds+60])
  
  fine_inds = {
    # (np.arange(9)*4 + n) % 9
    'Y0': np.array([1,5,0,4,8,3,7,2,6]),
    'Y1': np.array([8,3,7,2,6,1,5,0,4]),
    'M0': np.array([8,3,7,2,6,1,5,0,4]),
    'M1': np.array([1,5,0,4,8,3,7,2,6]),
    'C0': np.array([1,5,0,4,8,3,7,2,6]),
    'C1': np.array([8,3,7,2,6,1,5,0,4])
  }[channel]
  line = line.transpose()
  line[fine_inds,:] = line
  
  buf[:9,inds] = line
  return buf

def _pack_bits(bit_arr):
  """
  Parameters
  -----
  bit_arr: np.ndarray
  Bit array with dtype np.uint8 and elements being either 0 or 1.

  Returns
  -----
  byte_arr: bytes
  """
  
  assert(bit_arr.dtype == np.uint8)
  assert(np.all(bit_arr <= 1))
  assert(bit_arr.shape[-1] % 8 == 0)
  
  byte_arr = bit_arr.reshape(bit_arr.shape[:-1]+(-1, 8))
  byte_arr = (byte_arr << np.arange(8)).sum(-1, dtype=np.uint8)
  byte_arr = bytes(byte_arr.reshape(-1))
  return byte_arr

def _resize(img):
  import cv2
  
  h, w = img.shape[:2]
  scale = LINE_WIDTH/h
  img = cv2.resize(img, (int(w*scale), LINE_WIDTH))
  return img

def _cmy_array_to_lines(img):
  img_c = img[:,:,0]
  img_m = img[:,:,1]
  img_y = img[:,:,2]

  buf = np.empty([18,120], dtype=np.uint8)
  lines = []
  W = img.shape[1]
  for i in range(W + 2*COLOR_INTERVAL):
    buf[:] = 0

    i_c = i
    i_m = i - COLOR_INTERVAL
    i_y = i - 2*COLOR_INTERVAL
    if i_c >= 0 and i_c < W:
      #_add_line(buf, img_c[::-1,i_c], 'C1') left
      _add_line(buf, img_c[::-1,i_c], 'C0')
    if i_m >= 0 and i_m < W:
      #_add_line(buf, img_m[::-1,i_m], 'M0') left
      _add_line(buf, img_m[::-1,i_m], 'M1')
    if i_y >= 0 and i_y < W:
      #_add_line(buf, img_y[::-1,i_y], 'Y1') left
      _add_line(buf, img_y[::-1,i_y], 'Y0')
    line = _pack_bits(buf)
    assert(len(line) == 270), len(line)
    lines.append(line)
  return lines

def convert_to_mbd(img):
  img = _resize(img)

  img = 255 - img #RGB -> CMY
  img = _dither(img)
  lines = _cmy_array_to_lines(img)

  header = 'MBrush'.encode()
  header += bytes([0,0,0,2,0,0,0,0,0,0])
  mbd = bytes([0x00, 0x87]).join([header]+lines)
  return mbd
