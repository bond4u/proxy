#!/usr/bin/env python3
#
# Fake AniDB UDP server for testing
#
import socket
import time
import signal
import threading
import random
import SessId
import FileCache
import CalCache
import UpdateCache
import EpisodeCache
import GroupStatusCache
import MyListCache
import MyListStatsCache

# listening port
listPort = 9004
# maximum packet size to receive (udp is 1400 i think)
MAX_PKT_SIZE = 4*1024
# after first 5 packets
shortDelay = 2.500 # sec
# after 60 min
longDelay = 4.500 # sec
# after x sec idle, log out?
idleLogout = 6*60

# ctrl+c interrupt flag
global g_sigInt
g_sigInt = False

def sig_int_handler(signal, frame):
  global g_sigInt
  g_sigInt = True
  log("sig_int")

def log(s):
  print(time.ctime()+" server: "+s,flush=True)

def getCmd(data):
  '''Extract command from beginning on string'''
  cmd = ""
  i = data.find(" ")
  if -1 != i:
    # split command and args
    cmd = data[0:i]
    data = data[i+1:]
  else: # no args
    cmd = data
    data = ""
  return (cmd,data)

def handleNewClient(addr,data):
  '''Generate new client state data'''
  auth = ""
  sid = ""
  queue = []
  (cmd,args) = getCmd(data)
  if cmd == "AUTH":
    # respond to AUTH with 200 code and session
    auth = data
    sid = SessId.genSid()
    resp = "200 "+sid+" LOGIN ACCEPTED"
    queue.append(resp)
    ncd = { "AUTH": auth, "RESPS": queue, "SID": sid, "LASTRECV": time.time() }
  else: #some other command
    resp = "301 NOT LOGGED IN"
    queue.append(resp)
    ncd = { "RESPS": queue, "LASTRECV": time.time() }
  return ncd

log("main: start")
signal.signal(signal.SIGINT, sig_int_handler)

# listening socket for incoming client connections
listSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
listSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listSock.bind(("",listPort))
log("main: listening on port: "+str(listPort))

# listen for data 100 millisec then time out and do other stuff
listSock.settimeout(0.1)

#clients map
g_clnts = {}

g_fileCache = FileCache.FileCache("server-files.txt")
g_fileCache.load()

g_calCache = CalCache.CalCache("server-calendar.txt")
g_calCache.load()

g_updCache = UpdateCache.UpdateCache("server-updated.txt")
g_updCache.load()

g_episodeCache = EpisodeCache.EpisodeCache("server-episodes.txt")
g_episodeCache.load()

g_grStaCache = GroupStatusCache.GroupStatusCache("server-groupstatus.txt")
g_grStaCache.load()

g_myListCache = MyListCache.MyListCache("server-mylist.txt")
g_myListCache.load()

g_myLSCache = MyListStatsCache.MyListStatsCache("server-mystliststats.txt")
g_myLSCache.load()

log("main: waiting for data..")
while True != g_sigInt:
  data = None
  addr = None
  try:
    (data,addr) = listSock.recvfrom(MAX_PKT_SIZE)
    data = data.decode("ascii")
  except socket.timeout:
    # check for loop exit condition
    pass
  except KeyboardInterrupt:
    log("main: ctrl+c")
    continue
  if (None != data) and (None != addr):
    log("main: from: "+str(addr)+" received: "+str(data))
  if (None != data) and (None != addr) and (addr in g_clnts):
    # known client
    clnt = g_clnts[addr]
    auth = clnt["AUTH"]
    sid = clnt["SID"]
    lr = clnt["LASTRECV"]
    td = time.time() - lr
    log("main: known client, sessionId: "+sid+" timeDelta: "+str(td))
    if ("" != auth) and ("" != sid):
      #authenticated client - queue response
      (cmd,args) = getCmd(data)
      if "AUTH" == cmd:
        resp = "201 "+sid+" ALREADY LOGGED IN"
      elif "FILE" == cmd:
        args = SessId.removeSess(args)
        resp = g_fileCache.getFile(args)
        if None == resp:
          log("main: not in cache")
          resp = "302 NO SUCH FILE"
      elif "CALENDAR" == cmd:
        log("main: calendar: checking")
        resp = g_calCache.get()
        log("main: calendar: response: "+str(resp))
        if None == resp:
          log("main: calendar not in cache: dummy response")
          resp = "297 CALENDAR\n"
      elif "UPDATED" == cmd:
        log("main: updated: checking")
        resp = g_updCache.get(args)
        if None == resp:
          log("main: updates not in cache: dummy response")
          resp = "243 UPDATED\n1|213|432143|432,5432,43214"
      elif "EPISODE" == cmd:
        log("main: episode: checking")
        resp = g_episodeCache.get(args)
        if None == resp:
          log("main: episode not in cache: dummy response")
          resp = "241 EPISODE\n"
      elif "GROUPSTATUS" == cmd:
        log("main: group status: checking")
        resp = g_grStaCache.get(args)
        if None == resp:
          log("main: group status not in cache: dummy response")
          resp = "225 GROUPSTATUS\n"
      elif "MYLISTADD" == cmd:
        log("main: myList: checking")
        resp = g_myListCache.get(args)
        if None == resp:
          log("main: entry not in myList, adding..")
          resp = "210 MYLIST ENTRY ADDED\n"+str(random.randint(1,10000000))
          g_myListCache.set(args,resp)
      elif "MYLISTSTATS" == cmd:
        log("main: myListStats: checking")
        resp = g_myLSCache.get()
        if None == resp:
          log("main: no stats, generating random")
          resp = "222 MYLIST STATS\n"+"0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0|0\n"
      else: #some other command
        log("main: unknown cmd: '"+cmd+"'")
        resp = "desd"
      log("main: queueing response: "+str(resp))
      #listSock.sendto(resp,addr)
      rq = clnt["RESPS"]
      rq.append(resp)
    else:
      log("main: client not authenticated, ignoring")
  elif (None != data) and (None != addr):
    log("main: new client: "+str(addr))
    ncd = handleNewClient(addr,data)
    #log("main: new client state data: "+str(ncd))
    g_clnts[addr] = ncd
  #loop over clients
  for t in g_clnts:
    # check client for queued responses
    cl = g_clnts[t]
    r = cl["RESPS"]
    if 0 < len(r):
      d = r.pop(0)
      log("main: responding to: "+str(t)+" with: "+str(d))
      d = d.encode("ascii")
      listSock.sendto(d,t)

log("main: finishing..")
listSock.close()
log("main: done")
