import json
import socket
import sys
import time

#gives the option to get data from an external server instead and send that
#if no options given it will default to localhost instead
if len(sys.argv) == 3:
  socktype = socket.AF_INET
  sockaddr = (sys.argv[1], int(sys.argv[2]))
elif len(sys.argv) == 2:
  socktype = socket.AF_UNIX
  sockaddr = sys.argv[1]
else:
  socktype = socket.AF_UNIX
  sockaddr = "/var/run/yggdrasil.sock"

def getPeersRequest(key):
  return '{{"keepalive":true, "request":"debugGetPeers", "key":"{}"}}'.format(key)

def doRequest(req):
  try:
    ygg = socket.socket(socktype, socket.SOCK_STREAM)
    ygg.connect(sockaddr)
    ygg.send(req)
    data = json.loads(ygg.recv(1024*15))
    return data
  except:
    return None

visited = set() # Add nodes after a successful lookup response
rumored = set() # Add rumors about nodes to ping
timedout = set()
def handleResponse(address, data):
  global visited
  global rumored
  global timedout
  if address in visited: return
  if not data: return
  if 'response' not in data: return
  for k,v in data['response'].iteritems():
    if 'keys' not in v: continue
    keys = v['keys']
    for key in keys:
      if key in visited: continue
      if key in timedout: continue
      rumored.add(key)
  selfInfo = doRequest('{{"keepalive":true, "request":"debugGetSelf", "key":"{}"}}'.format(address))
  if 'response' not in selfInfo: return
  coords = None
  for _,v in selfInfo['response'].iteritems():
    if 'Coords' not in v: continue
    coords = str(v['Coords'])
    break
  if coords == None: return
  nodename = None
  nodeinfo = doRequest('{{"keepalive":true, "request":"getNodeInfo", "key":"{}"}}'.format(address))
  try:
    if nodeinfo and 'response' in nodeinfo and 'nodeinfo' in nodeinfo['response'] and 'name' in nodeinfo['response']['nodeinfo']:
      nodename = '"' + str(nodeinfo['response']['nodeinfo']['name']) + '"'
  except:
    pass
  now = time.time()
  if len(visited) > 0: sys.stdout.write(",\n")
  if nodename:
    sys.stdout.write('"{}": ["{}", {}, {}]'.format(address, coords, int(now), nodename))
  else:
    sys.stdout.write('"{}": ["{}", {}]'.format(address, coords, int(now)))
  sys.stdout.flush()
  visited.add(address)
# End handleResponse

# Get self info
selfInfo = doRequest('{"keepalive":true, "request":"getSelf"}')
for k,v in selfInfo['response']['self'].iteritems(): rumored.add(v['key'])

# Initialize dicts of visited/rumored nodes
#for k,v in selfInfo['response']['self'].iteritems(): rumored[k] = v

# Loop over rumored nodes and ping them, adding to visited if they respond
print '{"yggnodes": {'
while len(rumored) > 0:
  for k in rumored:
    handleResponse(k, doRequest(getPeersRequest(v['key'])))
    break
  rumored.remove(k)
print '\n}}'
#End

# TODO do something with the results

#print visited
#print timedout
