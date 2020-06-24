import urllib.request
import json

def _get(query, host='192.168.44.1'):
  url = f'http://{host}/cgi-bin/{query}'
  req = urllib.request.Request(url)

  with urllib.request.urlopen(req) as res:
    return json.loads(res.read().decode())

def _post(data, pos=None, filename=None, host='192.168.44.1'):
  url = f'http://{host}/cgi-bin/upload'

  boundary = '----SendMBDBoundary'
  header = {
    'Content-Type': 'multipart/form-data; boundary='+boundary
  }

  body = ''
  if pos is not None:
    body += '--' + boundary + '\r\n'
    body += f'Content-Disposition: form-data; name="pos"\r\n'
    body += '\r\n'
    body += f'{pos}\r\n'
  body += '--' + boundary + '\r\n'
  body += 'Content-Disposition: form-data; name="file"'
  if filename is not None:
    body += f'; filename="{filename}"'
  body += '\r\n'
  body += '\r\n'

  body1 = body

  body = ''
  body += '\r\n'

  body += '--' + boundary + '--\r\n'
  body2 = body
  #print(body1 + 'data' + body2)
  
  body = body1.encode() + data + body2.encode()
  req = urllib.request.Request(url, method='POST', headers=header, data=body)

  with urllib.request.urlopen(req) as res:
    return json.loads(res.read().decode())

def get_info(host='192.168.44.1'):
  return _get('cmd?cmd=get_info', host=host)

def upload(data, filename='0.mbd', host='192.168.44.1'):
  block_size = 128*1024
    
  res = _get('cmd?cmd=rm_upload', host=host)
  if res['status'] != 'ok':
    raise IOError('Failed to clear the upload directory.')

  pos = 0
  while True:
    block = data[pos : pos+block_size]
    if not block:
      break
    
    res = _post(block, pos=pos, filename=filename, host=host)
    if res['status'] != 'ok':
      raise IOError('Failed to send the data.')
  
    pos += block_size

  res = _get('cmd?cmd=sync', host=host)
  if res['status'] != 'ok':
    raise IOError('Failed to synchronize.')
