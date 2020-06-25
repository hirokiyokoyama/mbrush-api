#!/usr/bin/env python3

import numpy as np

LINE_WIDTH = 360
#COLOR_INTERVAL = 32
COLOR_OFFSETS = [
  36*2, 36*2+10, 36+10, 36, 0, 10
]

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

def _arrange_line(line):
  """
  line: np.ndarray
    Binary image column from bottom to top
    with shape [180,12] and dtype np.uint8,
    each element of which is either 0 or 1.
  """
  
  assert(line.dtype == np.uint8)
  assert(line.shape == (180,12))
  assert(np.all(line <= 1))
  
  inds = np.array([0,10,1,11,2,12,3,13,4,14])
  inds = inds[np.newaxis] + np.reshape([0,5,20,25,40,45,0,5,20,25,40,45], [12,1])
  inds = np.concatenate([inds, inds+60], axis=1)
  
  fine_inds = np.array([
    # (np.arange(9)*4 + n) % 9
    [1,5,0,4,8,3,7,2,6],
    [8,3,7,2,6,1,5,0,4],
    [8,3,7,2,6,1,5,0,4],
    [1,5,0,4,8,3,7,2,6],
    [1,5,0,4,8,3,7,2,6],
    [8,3,7,2,6,1,5,0,4],
    
    [6,1,5,0,4,8,3,7,2],
    [8,3,7,2,6,1,5,0,4],
    [8,3,7,2,6,1,5,0,4],
    [6,1,5,0,4,8,3,7,2],
    [6,1,5,0,4,8,3,7,2],
    [8,3,7,2,6,1,5,0,4],
  ])
  buf = np.zeros([18,120], dtype=np.uint8)
  line = line.reshape(20,9,12).transpose(2,1,0).copy()
  for i in range(12):
    line[i,fine_inds[i],:] = line[i].copy()

    if i < 6:
      buf[:9,inds[i]] = line[i]
    else:
      buf[9:,inds[i]] = line[i]
  assert(np.all(buf <= 1))
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
  byte_arr = byte_arr << np.arange(8)
  byte_arr = byte_arr.sum(-1, dtype=np.uint8)
  byte_arr = bytes(byte_arr.reshape(-1))
  return byte_arr

def _resize(img):
  import cv2
  
  h, w = img.shape[:2]
  if h == LINE_WIDTH:
    return img
  scale = LINE_WIDTH/h
  img = cv2.resize(img, (int(w*scale), LINE_WIDTH))
  return img

def _cmy_array_to_lines(img, color_offsets=None):
  if color_offsets is None:
    color_offsets = COLOR_OFFSETS
    
  img_yl = img[-1::-2,:,2]
  img_yr = img[-2::-2,:,2]
  img_ml = img[-1::-2,:,1]
  img_mr = img[-2::-2,:,1]
  img_cl = img[-1::-2,:,0]
  img_cr = img[-2::-2,:,0]

  lines = []
  W = img.shape[1]
  for i in range(W + max(color_offsets)):
    i_yr = i - color_offsets[0]
    i_yl = i - color_offsets[1]
    i_ml = i - color_offsets[2]
    i_mr = i - color_offsets[3]
    i_cr = i - color_offsets[4]
    i_cl = i - color_offsets[5]
    buf = np.zeros([LINE_WIDTH//2,12], dtype=np.uint8)
    if i_yr >= 0 and i_yr < W:
      buf[:,0] = img_yr[:,i_yr]
      #buf[:,0+6] = img_yr[:,i_yr]
    if i_yl >= 0 and i_yl < W:
      buf[:,1] = img_yl[:,i_yl]
      #buf[:,1+6] = img_yl[:,i_yl]
    if i_ml >= 0 and i_ml < W:
      buf[:,2] = img_ml[:,i_ml]
      #buf[:,2+6] = img_ml[:,i_ml]
    if i_mr >= 0 and i_mr < W:
      buf[:,3] = img_mr[:,i_mr]
      #buf[:,3+6] = img_mr[:,i_mr]
    if i_cr >= 0 and i_cr < W:
      buf[:,4] = img_cr[:,i_cr]
      #buf[:,4+6] = img_cr[:,i_cr]
    if i_cl >= 0 and i_cl < W:
      buf[:,5] = img_cl[:,i_cl]
      #buf[:,5+6] = img_cl[:,i_cl]
    buf = _arrange_line(buf)
    line = _pack_bits(buf)
    assert(len(line) == 270), len(line)
    lines.append(line)
  return lines

def convert_to_mbd(img, color_offsets=None):
  img = _resize(img)

  img = 255 - img #RGB -> CMY
  img = _dither(img)
  lines = _cmy_array_to_lines(img, color_offsets=color_offsets)

  header = 'MBrush'.encode()
  header += bytes([0,0,0,2,0,0,0,0,0,0])
  mbd = bytes([0x00, 0x87]).join([header]+lines)
  return mbd
