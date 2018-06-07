#!/usr/bin/env python3
#
# Fake AniDB client for testing
#
import socket
import time

def log(s):
  print(time.ctime()+" client1: "+s,flush=True)

log("main: start")
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# local UDP proxy i'm testing
sockPort = 9002
sock.connect(("",sockPort))
log("main: socket connected..")
# wait for replay 30 seconds
sockTimeout = 30
sock.settimeout(sockTimeout)
# udp packet size is 1400 or something
MAX_PACKET_SIZE = 4*1024

def send(sock,req):
  log("main: sending: "+req)
  try:
    d = req.encode("ascii")
    r = sock.send(d)
    if r != len(req):
      log("send.rval: "+str(r))
    #else successful send
  except socket.timeout:
    log("send.timeout")
  return r

def recv(sock):
  try:
    r = sock.recv(MAX_PACKET_SIZE)
    r = r.decode("ascii")
    log("recv.rval: "+r)
  except socket.timeout:
    r = None
    log("recv.timeout")
  #except KeyboardInterrupt:
  #  r = None
  #  log("recv interrupted by ctrl+c")
  return r

def getCode(s):
  c = ""
  i = s.find(" ")
  if -1 != i:
    c = s[0:i]
  return c

def getSessId(s):
  v = s.split(" ")
  return v[1]

req = "AUTH user=me&pass=me&protover=3&client=ommserver&clientver=2&comp=1"
while True:
  r = send(sock,req)
  #200 JIDFx LOGIN ACCEPTED
  resp = recv(sock)
  if None != resp:
    code = getCode(resp)
    if "200" == code:
      g_sessId = getSessId(resp)
      break # success
  time.sleep(1)
  #else keep trying

req = "UPDATED entity=1&time=1520027449&s="
req += g_sessId
send(sock,req)

recv(sock)

time.sleep(1)

req = "FILE size=8429&ed2k=C2FAD4A41C26FD8840A72350C9A10A47&fmask=7FF8FFF9FE&amask=0000FCC0&s="
req += g_sessId
send(sock,req)

#220 FILE 1567019|6287|96447|10434|221747530||0|1|8429|c2fad4a41c26fd8840a72350c9a10a47|0f0073e54742a4c59710d6eef98a9df6|99e5ac1bf7d4fcf7fb9d7dcf7c6ea40e700ca78d|9a70fefd|high|DVD|unknown|0|unknown|0|0x0|mkv|english|japanese|0||1231977600|Abunai Sisters: Koko & Mika - 01 - Abunai Beach - [tabenokoshi](9a70fefd).mkv|2|0|0|0||||01|Abunai Beach|Abunai Beach|Abunai Beach|106|1|tabenokoshi|tabenokoshi
recv(sock)

time.sleep(1)

req = "PING"
send(sock,req)

#300 PONG
recv(sock)

time.sleep(1)

req = "FILE size=195290750&ed2k=B1E8BDDF19656086F289079DFA53ABFD&fmask=7FF8FFF9FE&amask=0000FCC0&s="
req += g_sessId
send(sock,req)

#220 FILE 1960096|1913|28173|0|240045754||0|0|195290750|b1e8bddf19656086f289079dfa53abfd|ab1e2fbb23fb495d6b5ddddec49af5b2|20bad69dae904fb6023eefbdcc1d71b031902507|78c4e927|med|DVD|unknown|0|unknown|0|0x0|mkv|japanese|none|0||225676800|Candy Candy - 021 - A Pigeon that Carried Friendship - [RAW](78c4e927).mkv|2|0|0|0||||021|A Pigeon that Carried Friendship|Yuujou o Tsutaeru Hato|<E5><8F><8B><E6><83><85><E3><82><92><E4><BC><9D><E3><81><88><E3><82><8B><E9><B3><A9>|400|1|raw/unknown|raw
recv(sock)

time.sleep(1)

req = "CALENDAR s="
req += g_sessId
send(sock,req)

recv(sock)

time.sleep(1)

req = "EPISODE eid=149777&s="
req += g_sessId
send(sock,req)

recv(sock)

time.sleep(1)

req = "EPISODE eid=149791&s="
req += g_sessId
send(sock,req)

recv(sock)

time.sleep(1)

req = "GROUPSTATUS aid=1503&s="
req += g_sessId
send(sock,req)

recv(sock)

time.sleep(1)

req = "GROUPSTATUS aid=1052&s="
req += g_sessId
send(sock,req)

recv(sock)

time.sleep(1)

req = "MYLISTADD size=1375035134&ed2k=505433F2DB67DAD75C89F35FB19FB5BD&viewed=0&state=2&s="
req += g_sessId
send(sock,req)

recv(sock)

time.sleep(1)

req = "MYLISTADD size=1360892744&ed2k=DBBB85D58FC4768DF56F71345B000BF6&viewed=0&state=2&s="
req += g_sessId
send(sock,req)

recv(sock)

time.sleep(1)

req = "MYLISTSTATS s="
req += g_sessId
send(sock,req)

recv(sock)

time.sleep(1)

req = "LOGOUT s="+g_sessId
send(sock,req)

#203 LOGGED OUT
recv(sock)

sock.close()
log("main: done")
