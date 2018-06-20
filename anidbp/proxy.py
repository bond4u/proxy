#!/usr/bin/env python3
#
# anidb UDP proxy
#
import socket
import time
import signal
import threading
import SyncQueue
import SessId
import FileCache
import CalCache
import UpdateCache
import EpisodeCache
import GroupStatusCache
import MyListCache
import MyListStatsCache
import zlib
import traceback
import os
import sys

# proxy listening port
listPort = 9000
#listPort = 9002
# listening time 0.1 sec
listTimeout = 0.1
# maximum packet size to receive (udp is 1400 i think)
MAX_PKT_SIZE = 4*1024
# client socket to server
#TODO re-use same socket to avoid AniDB countermeasures
#ANIDB_HOST="" # local
ANIDB_HOST="api.anidb.info"
ANIDB_PORT=9000
#ANIDB_PORT=9004

# incoming requests synchronized queue
global g_reqs
g_reqs = SyncQueue.SyncQueue()

# outgoing responses queue
global g_resps
g_resps = SyncQueue.SyncQueue()

# ctrl+c interrupt flag
global g_sigInt
g_sigInt = False

def sig_int_handler(sig, frame):
  log("sig "+str(sig))
  traceback.print_stack(frame)
  global g_sigInt
  g_sigInt = True

def log(s,fallback=True):
  # attempting to print utf stuff, may fail
  try:
    #i = s.find("&pass=")
    #if -1 != i:
      #remove password, obv pwd with & is gonna mess things up
    #  z = s[i+1:]
    #  j = z.find("&")
    #  s = s[:i+1]+z[j:]
    print(time.ctime()+" udpProxy: "+s,flush=True)
  except (TypeError,UnicodeError,UnicodeEncodeError,UnicodeDecodeError) as err:
    if not fallback:
      raise err
    z = bytes(s,"utf-8")
    print(time.ctime()+" udpProxy: bytes: "+str(z),flush=True)

log("main: start")
signal.signal(signal.SIGHUP, sig_int_handler)
signal.signal(signal.SIGINT, sig_int_handler)
signal.signal(signal.SIGQUIT, sig_int_handler)
signal.signal(signal.SIGTERM, sig_int_handler)

# listening socket for incoming client connections
listSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
listSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
listSock.bind(("",listPort))
log("main: listening on port: "+str(listPort))

# listen for data 1 sec then time out and check exit condition
listSock.settimeout(listTimeout)

global g_cSess
g_cSess = {}

# loading data files makes startup process several minutes long
# probably because excessive logging
#global g_fileCache
#g_fileCache = FileCache.FileCache("proxy-files-cache.txt")
#g_fileCache.load()

global g_calCache
g_calCache = CalCache.CalCache("proxy-calendar-cache.txt")
g_calCache.load()

global g_updCache
g_updCache = UpdateCache.UpdateCache("proxy-updated-cache.txt")
g_updCache.load()

global g_epiCache
g_epiCache = EpisodeCache.EpisodeCache("proxy-episode-cache.txt")
g_epiCache.load()

global g_grStaCache
g_grStaCache = GroupStatusCache.GroupStatusCache("proxy-groupstatus-cache.txt")
g_grStaCache.load()

global g_myListCache
g_myListCache = MyListCache.MyListCache("proxy-mylist-cache.txt")
g_myListCache.load()

global g_myLSCache
g_myLSCache = MyListStatsCache.MyListStatsCache("proxy-myliststats-cache.txt")
g_myLSCache.load()

def inflate(data,level=0):
  decompr = zlib.decompressobj(level + zlib.MAX_WBITS)
  infl = decompr.decompress(data)
  infl += decompr.flush()
  return infl

def det_enc(s):
  encs = ["utf-16-le","utf-16-be","utf-16","utf-8"]
  d = {}
  #log("det_enc in: "+str(s))
  for enc in encs:
    try:
      d[enc] = s.decode(enc)
      log("det_enc: "+enc+": "+str(d[enc]),fallback=False)
    except (UnicodeError,UnicodeDecodeError,UnicodeEncodeError):
      d[enc] = None
      #log("det_enc: "+enc+": failed")
    #log("det_enc: "+enc+": "+str(None!=d[enc]))
  for enc in encs:
    if None!=d[enc]:
      break
  #log("det_enc: rval: "+enc)
  return enc

def getCmd(s):
  '''Returns command from beginning of the data string'''
  cmd = ""
  if None==s:
    log("getCmd: string is None")
  i = s.find(" ")
  if -1 != i:
    cmd = s[:i]
    s = s[i+1:]
  else: # no args, like PING
    cmd = s
    s = ""
  return (cmd,s)

def getRespCode(s):
  '''Returns response code and text'''
  code = ""
  if None==s:
    log("getRespCode: string is None")
  i = s.find(" ")
  if -1 != i:
    code = s[:i]
    s = s[i+1:]
  else: #just code only
    code = s
    s = ""
  return (code,s)

def readFile(fn):
  '''Attempts to read from file, returns data,c_time,m_time triplet'''
  log("readFile: "+fn)
  if os.access(fn, os.R_OK):
    a = os.stat(fn)
    log("readFile: accessible: "+str(a))
    try:
      f = open(fn,"b+r")
      d = f.read()
      f.close()
    except:
      log("readFile: error: "+str(sys.exc_info()))
      raise
    triplet = (d,a.st_ctime,a.st_mtime)
  else:
   log("readFile: file is not accessible")
   triplet = (None,None,None)
  return triplet

def writeFile(fn,d):
  '''Creates a file with data'''
  log("writeFile: "+fn)
  try:
    p = os.path.dirname(fn)
    os.makedirs(p,exist_ok=True)
    f = open(fn,"b+w")
    w = f.write(d)
    f.close()
    log("writeFile: "+str(w)+" of "+str(len(d))+" written")
  except:
    log("writeFile: error: "+str(sys.exc_info()))
    raise

class SrvConnThrd(threading.Thread):
  '''Client socket to server with thread'''
  def __init__(self,server,port,reqs,resps):
    '''Set up connection properties'''
    threading.Thread.__init__(self)
    self.sock = None
    self.server = server
    self.port = port
    self.reqs = reqs
    self.resps = resps
    self.stopFlag = False
    self.sendTime = None
    self.recvTime = None
    self.sending = None
    self.sessId = None
    self.shortDelay = 2.500
    self.shortPeriod = 60*60 # 1h
    self.longDelay = 4.500
    self.idleDelay = 60*30
    self.shortStart = None
    self.longStart = None
    self.enc = "utf-8"
  def log(self,s):
    '''Logging method'''
    log("SrvConnThrd: "+s)
  def connect(self):
    '''Connects to server'''
    self.log("opening socket to server...")
    self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    self.sock.connect((self.server,self.port))
    self.sock.settimeout(0.1) # 0.1sec=100ms
  def disconnect(self):
    '''Disconnects from server'''
    self.log("shutting down socket to server")
    self.sock.close()
    self.sock = None
    self.sessId = None
    self.sending = None
  def send(self,data,addr):
    '''Sends data to server'''
    self.log("sending to server: "+data)
    try:
      data = data.encode("utf-8")
      #self.log("send: unicode encode ok")
    except (UnicodeError,UnicodeEncodeError) as err:
      self.log("send: unicode encode error: "+str(err))
    try:
      r = self.sock.send(data)
      #self.log("sent: "+str(r))
    except socket.timeout:
      self.log("send timeout")
      r = None
    #TODO other exceptions
    self.sendTime = time.time()
    return r
  def recv(self):
    '''Receives any data from server, returns text,binary pair'''
    txtdata = None
    if None != self.sock:
      try:
        bindata = self.sock.recv(MAX_PKT_SIZE)
        self.recvTime = time.time()
        if 0==bindata[0] and 0==bindata[1]:
          try:
            #self.log("recv: 0,0 inflating..")
            data = inflate(bindata[2:])
            #self.log("recv: inflated '"+str(data)+"'")
          except:
            self.log("recv: inflate error")
        else:
          data = bindata
        enc = det_enc(data)
        self.log("recv: enc: "+enc+" type: "+str(type(data)))
        try:
          txtdata = data.decode("utf-8")
          #self.log("recv: unicode decode ok")
        except UnicodeError as err:
          self.log("recv: unicode decode error: "+str(err))
        # print uses ascii coding and that cant print unicode
        self.log("received from server: "+str(txtdata))
      except socket.timeout:
        bindata = None
      except ConnectionRefusedError:
        bindata = None
        self.disconnect()
    else: # no connection yet
      bindata = None
      time.sleep(0.1) # just sleep a bit
    return (txtdata,bindata)
  def login(self):
    if None == self.sessId:
      global g_cSess
      l = len(g_cSess)
      self.log("login: client sessions: "+str(l))
      key = next(iter(g_cSess))
      sessData = g_cSess[key]
      self.log("login: using 1st sessData: "+str(sessData))
      # AUTH response is for us only, we dont forward it to client
      addr = None # sessData["ADDR"]
      # removeSess also removes encoding and we'll use our own
      data = SessId.removeSess(sessData["DATA"]) + "&enc="+self.enc
      sid = sessData["SID"]
      self.log("login: sid: "+sid+" addr: "+str(addr)+" data: "+str(data))
      self.sending = (data,addr)
      self.send(data,addr)
  def run(self):
    '''Thread loop'''
    global g_sigInt
    while (False == self.stopFlag) and (False == g_sigInt):
      tresp = None
      bresp = None
      if None == self.sending:
        # have not sent anything
        cooldown = True
        now = time.time()
        if None == self.recvTime:
          #self.log("run: no previous recv, sending now")
          cooldown = False
        elif (None != self.shortStart) and (self.shortStart+self.shortPeriod > now):
          # use short delay
          if self.recvTime+self.shortDelay < now:
            cooldown = False
          #else:
            #self.log("run: short delay since "+str(self.recvTime))
        elif (None != self.shortStart) and (self.shortStart+self.shortPeriod < now):
          # use long delay
          if self.recvTime+self.longDelay < now:
            cooldown = False
          #else:
            #self.log("run: long delay since "+str(self.recvTime))
        if not cooldown and (0 < self.reqs.size()):
          if None == self.shortStart:
            self.shortStart = time.time()
          if None == self.sock:
            self.connect()
          elif None == self.sessId:
            self.login()
          else:
            t = self.reqs.get()
            if None != t:
              (req,addr) = t
              # some commands require session
              if ("FILE "==req[:5]) or ("UPDATED "==req[:8]) or ("MYLISTADD "==req[:10]) \
or ("CALENDAR"==req) or ("CALENDAR "==req[:9]) or ("GROUPSTATUS "==req[:12]) \
or ("MYLISTSTATS"==req) or ("MYLISTSTATS "==req[:12]):
                if not " " in req:
                  req += " "
                req += "&s="+self.sessId
                t = (req,addr)
              self.sending = t
              self.send(req,addr)
        else: #nothing to send, sleep on socket
          (tresp,bresp) = self.recv()
      else: #sent request, wait for response
        self.log("sent something, waiting for response")
        (tresp,bresp) = self.recv()
      if (None != self.sending) and (None != tresp):
        # got response, do we had timeout and need to re-login?
        (code,text) = getRespCode(tresp)
        self.log("run: code '"+str(code)+"'") #, '"+str(text)+"'")
        (req,addr) = self.sending
        self.log("run: req '"+str(req)+"', '"+str(addr)+"'")
        (cmd,params) = getCmd(req)
        self.log("run: cmd '"+str(cmd)+"', '"+str(params)+"'")
        if "501"==code:
          req = SessId.removeSess(req)
          self.log("501: clearing sessId: "+str(req))
          self.sessId = None
          t = (req,addr)
          self.reqs.insertFront(t)
          self.log("req re-added: "+str(self.reqs.size()))
          req = None
          tresp = None
          bresp = None
          cmd = ""
        if "AUTH" == cmd:
          vals = tresp.split(" ",2)
          # 1st is code, 2nd is session, rest is text
          self.sessId = vals[1]
          self.log("using session id: "+self.sessId+", addr: "+str(addr))
          addr = None
        elif "FILE" == cmd:
          self.log("adding to fileCache: '"+str(params)+"', '"+str(tresp)+"'")
          #global g_fileCache
          #g_fileCache.addFile(params,resp,True)
          fn = "FILE/"+SessId.removeSess(params)
          writeFile(fn,bresp)
        elif "CALENDAR" == cmd:
          self.log("adding to calCache")
          global g_calCache
          g_calCache.set(tresp,True)
        elif "UPDATED" == cmd:
          self.log("adding to updCache")
          global g_updCache
          g_updCache.set(params,tresp,True)
        elif "EPISODE" == cmd:
          self.log("adding to epiCache")
          global g_epiCache
          g_epiCache.set(params,tresp,True)
        elif "GROUPSTATUS" == cmd:
          self.log("adding to grStaCache")
          global g_grStaCache
          g_grStaCache.set(params,tresp,True)
        elif "MYLISTADD" == cmd:
          self.log("adding to myListCache")
          global g_myListCache
          g_myListCache.set(params,tresp,True)
        elif "MYLISTSTATS" == cmd:
          self.log("adding to myListStatsCache")
          global g_myLSCache
          g_myLSCache.set(tresp,True)
        if (None != tresp) and (None != addr):
          # some utf chars can't be printed out in ascii
          self.log("queuing to: "+str(addr)+" response: "+str(tresp))
          self.resps.add((tresp,addr,None))
          self.log("resps queue size: "+str(self.resps.size()))
        else:
          self.log("no resp or no addr")
        self.sending = None
      elif (None != self.sending) and (None == tresp):
        if (None != self.sendTime) and (None == self.recvTime or self.sendTime > self.recvTime):
          delta = time.time() - self.sendTime
          if 60 <= delta:
            self.log("no response from server for 60 sec, resetting")
            t = self.sending
            self.sending = None
            self.reqs.insertFront(t)
            self.log("req re-added: "+str(self.reqs.size()))
            req = None
  def stop(self):
    '''Sets thread stop flag'''
    self.stopFlag = True

global g_cltSock
g_cltSock = SrvConnThrd(ANIDB_HOST,ANIDB_PORT,g_reqs,g_resps)
log("main: starting server connection thread..")
g_cltSock.start()

def doRefresh(cmd,idate,udate):
  r = True
  h24 = 24*60*60 # 24 hours is how many seconds?
  log("doRefresh: start: "+str(idate)+", "+str(udate))
  if (None == udate) or (idate == udate):
    # wait at least 24h before refreshing again
    r = (idate+h24) < time.time()
    log("doRefresh: over 24h have passed since "+cmd+" IDATE: "+str(r))
  else:
    # dont refresh if updated recently (within 24h)
    r = (udate+2*h24) < time.time()
    log("doRefresh: over 48h have passed since "+cmd+" UDATE: "+str(r))
  return r

def handleClient(data,addr,pEnc):
  global g_cSess
  sessData = g_cSess[addr]
  sessId = sessData["SID"]
  if None==pEnc:
    pEnc = sessData["ENC"]
  (cmd,params) = getCmd(data)
  log("handleClient: "+str(addr)+" '"+pEnc+"' sessId: '"+sessId+"' cmd: '"+cmd+"'")
  global g_reqs
  global g_resps
  if "AUTH" == cmd:
    resp = "201 "+sessId+" LOGIN EXISTED"
    log("handleClient: AUTH response: "+resp)
    g_resps.add((resp,addr,"utf-8"))
  elif "PING" == cmd:
    resp = "300 PONG"
    log("handleClient: PING response: "+resp)
    g_resps.add((resp,addr,"utf-8"))
  elif "FILE" == cmd:
    #global g_fileCache
    #(req,resp,idate,udate) = g_fileCache.parse(params)
    req = SessId.removeSess(params)
    #log("handleClient: FILE: params '"+str(params)+"', '"+str(req)+"'")
    #resp = g_fileCache.getFile(req)
    (bresp,idate,udate) = readFile("FILE/"+req)
    #log("handleClient: FILE: resp '"+str(resp)+"'")
    req2 = cmd+" "+req
    if None == bresp:
      log("handleClient: not in fileCache, queue to server: "+str(req2))
      g_reqs.add((req2,addr))
    else:
      #log("handleClient: checking fileCache dates")
      #(idate,udate) = g_fileCache.getFileDates(req)
      if doRefresh(cmd,idate,udate):
        log("handleClient: fileCached data is old, refreshing: "+str(req2))
        g_reqs.add((req2,addr))
      else:
        log("handleClient: using fileCache response")
        #have to convert bytes from file to text and then to client encoding
        tresp = bresp.decode("utf-8")
        g_resps.add((tresp,addr,pEnc))
  elif "LOGOUT" == cmd:
    if "s=" == params[:2]:
      if params[2:] == sessId:
        del g_cSess[addr]
        resp = "203 LOGGED OUT"
      else:
        resp = "303 WRONG SESSION GIVEN"
    else:
      resp = "304 NO SESSION GIVEN"
    g_resps.add((resp,addr,pEnc))
  elif "CALENDAR" == cmd:
    global g_calCache
    resp = g_calCache.get()
    if None == resp:
      log("handleClient: not in calCache: queue to server")
      g_reqs.add((cmd,addr))
    else:
      log("handleClient: checking calCache dates")
      (idate,udate) = g_calCache.getDates()
      if doRefresh(cmd,idate,udate):
        log("handleClient: calCache data is old, refreshing")
        g_reqs.add((cmd,addr))
      else:
        log("handleClient: using calCache response")
        g_resps.add((resp,addr,pEnc))
  elif "UPDATED" == cmd:
    global g_updCache
    req = cmd+" "+SessId.removeSess(params)
    resp = g_updCache.get(params)
    if None == resp:
      log("handleClient: not in updCache: queue to server")
      g_reqs.add((req,addr))
    else:
      log("handleClient: check updCache dates")
      (idate,udate) = g_updCache.getDates()
      if doRefresh(cmd,idate,udate):
        log("handleClient: updCache data is old, refreshing")
        g_reqs.add((req,addr))
      else:
        log("handleClient: using updCache response")
        g_resps.add((resp,addr,pEnc))
  elif "EPISODE" == cmd:
    global g_epiCache
    resp = g_epiCache.get(params)
    req = cmd+" "+SessId.removeSess(params)
    if None == resp:
      log("handleClient: not in epiCache: queue to server")
      g_reqs.add((req,addr))
    else:
      log("handleClient: check epiCache dates")
      (idate,udate) = g_epiCache.getDates(params)
      if doRefresh(cmd,idate,udate):
        log("handleClient: epiCache data is old, refreshing")
        g_reqs.add((req,addr))
      else:
        log("handleClient: using epiCache response")
        g_resps.add((resp,addr,pEnc))
  elif "GROUPSTATUS" == cmd:
    global g_grStaCache
    req = cmd+" "+SessId.removeSess(params)
    resp = g_grStaCache.get(params)
    if None == resp:
      log("handleClient: not in grStaCache: queue to server")
      g_reqs.add((req,addr))
    else:
      log("handleClient: check grStaCache dates")
      (idate,udate) = g_grStaCache.getDates(params)
      if doRefresh(cmd,idate,udate):
        log("handleClient: grStaCache data is old, refreshing")
        g_reqs.add((req,addr))
      else:
        log("handleClient: using grStaCache response")
        g_resps.add((resp,addr,pEnc))
  elif "MYLISTADD" == cmd:
    global g_myListCache
    req = cmd+" "+SessId.removeSess(params)
    resp = g_myListCache.get(params)
    if None == resp:
      log("handleClient: file not in MyList, sending to server")
      g_reqs.add((req,addr))
    else:
      log("handleClient: checking myListCache dates")
      (idate,udate) = g_myListCache.getDates(params)
      if doRefresh(cmd,idate,udate):
        log("handleClient: myListCache data is old, refreshing")
        g_reqs.add((req,addr))
      else:
        log("handleClient: using myListCache response")
        g_resps.add((resp,addr,pEnc))
  elif "MYLISTSTATS" == cmd:
    global g_myLSCache
    resp = g_myLSCache.get()
    if None == resp:
      log("handleClient: no data in MyListStats cache, sending to server")
      g_reqs.add((cmd,addr))
    else:
      log("handleClient: checking myListStatsCache dates")
      (idate,udate) = g_myLSCache.getDates()
      if doRefresh(cmd,idate,udate):
        log("handleClient: myLSCache data is old, refrshing")
        g_reqs.add((cmd,addr))
      else:
        log("handleClient: using myListStatsCache response")
        g_resps.add((resp,addr,pEnc))
  else:
    log("handleClient: unknown cmd: "+cmd)

def getEnc(s):
  e = "utf-8"
  p = s.split("&")
  for a in p:
    if "enc=" == a[:4]:
      e = a[4:]
  return e

log("main: waiting for clients..")
while False==g_sigInt:
  try:
    data,addr = listSock.recvfrom(MAX_PKT_SIZE)
    dEnc = det_enc(data)
    log("main: detected enc: "+dEnc)
    # ternary: data = data16 if None!=data16 else data8
  except socket.timeout:
    data = None
  if None!=data:
    #log("main: decoding "+dEnc)
    data = data.decode(dEnc)
    #log("main: decoded: "+dEnc)
    if addr in g_cSess:
      sd = g_cSess[addr]
      pEnc = sd["ENC"]
      if pEnc != dEnc:
        log("main: detected encoding '"+dEnc+"' does not match specified encoding '"+pEnc+"'")
      log("main: known client: "+str(addr)+" '"+dEnc+"' recv: "+data)
      sd["ENC2"] = dEnc
      handleClient(data,addr,dEnc)
    else:
      log("main: new client: "+str(addr)+" '"+dEnc+"' recv: "+data)
      (cmd,dat) = getCmd(data)
      if "AUTH" == cmd:
        sid = SessId.genSid()
        pEnc = getEnc(dat)
        sessData = { "ADDR": addr, "DATA": data, "SID": sid, "INTIME": time.time(), "ENC": pEnc }
        g_cSess[addr] = sessData
        log("main: client sessions: "+str(len(g_cSess)))
        resp = "200 "+sid+" LOGIN ACCEPTED"
      else:
        resp = "301 NOT LOGGED IN"
      g_resps.add((resp,addr,dEnc))
    #log("main: added to queue: "+str(g_reqs.size()))
  #else no data received
  t = g_resps.get()
  if None != t:
    (resp,addr,pEnc) = t
    log("main: resp: '"+str(addr)+"', enc: '"+str(pEnc)+"', resp: "+str(resp))
    if addr in g_cSess:
      sd = g_cSess[addr]
      #log("main: respond session: "+str(sd))
      if None == pEnc:
        if None != sd["ENC2"]:
          pEnc = sd["ENC2"]
          log("main: resp sess temp enc: "+str(pEnc))
          del sd["ENC2"]
        else:
          pEnc = sd["ENC"]
          log("main: resp sess enc: "+str(pEnc))
      else:
        log("main: resp enc: "+str(pEnc))
    else:
      log("addr "+str(addr)+" not known")
    log("main: responding to: "+str(addr)+" '"+str(pEnc)+"' with: "+str(resp))
    resp = resp.encode(pEnc)
    try:
      listSock.sendto(resp,addr)
    except socket.timeout:
      log("main: send to client timed out: "+str(addr))
  #else nothing to respond

log("main: finishing..")
listSock.close()
log("main: done")
