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
def handleResponse(publicKey, data):
  global visited
  global rumored
  global timedout
  if publicKey in visited: return
  if not data: return
  if 'response' not in data: return
  out = dict()
  for addr,v in data['response'].iteritems():
    if 'keys' not in v: continue
    peers = v['keys']
    for key in peers:
      if key in visited: continue
      if key in timedout: continue
      rumored.add(key)
    out['address'] = addr
    out['peers'] = peers
    break
  selfInfo = doRequest('{{"keepalive":true, "request":"debugGetSelf", "key":"{}"}}'.format(publicKey))
  if 'response' in selfInfo:
    for _,v in selfInfo['response'].iteritems():
      if 'coords' in v:
        out['coords'] = v['coords']
  dhtInfo = doRequest('{{"keepalive":true, "request":"debugGetDHT", "key":"{}"}}'.format(key))
  if 'response' in dhtInfo:
    for _,v in dhtInfo['response'].iteritems():
      if 'keys' in v:
        out['dht'] = v['keys']
  nodeInfo = doRequest('{{"keepalive":true, "request":"getNodeInfo", "key":"{}"}}'.format(publicKey))
  if 'response' in nodeInfo:
    for _,v in nodeInfo['response'].iteritems():
      out['nodeinfo'] = v
  out['time'] = time.time()
  if len(visited) > 0: sys.stdout.write(",\n")
  sys.stdout.write('"{}": {}'.format(publicKey, json.dumps(out)))
  sys.stdout.flush()
  visited.add(publicKey)
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
