#!/usr/bin/env python3
#
# HTTP proxy for tvdb, trakt, etc
#
import time
import os
import http.server
import socketserver
import http.client
import select
import threading
import socketserver
import ssl
import datetime

PROXY_PORT=80
PROXY_PORT2=9001
PROXY_PORT3=443

def log(s):
  frm = "%Y-%m-%d %H:%M:%S.%f"
  tid = threading.get_ident()
  tm = datetime.datetime.now().strftime(frm)
  try:
    print(tm+" "+str(tid)+" httpProxy: "+s,flush=True)
  except (TypeError,UnicodeError,UnicodeEncodeError,UnicodeDecodeError) as err:
    print(tm+" "+str(tid)+" httpProxy: "+bytes(s,"utf-8"),flush=True)

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
  """Proxy class"""
  def __init__(self,req,cli,srv):
    """Initializes class instance"""
    #log("__init__(self="+str(self)+", req="+str(req)+", cli="+str(cli)+", srv="+str(srv)+")")
    self.jmm = None
    self.img7 = None
    self.adb = None
    self.tvdb = None
    self.cwd = os.getcwd()
    #log("__init__: cwd="+str(self.cwd))
    super().__init__(req,cli,srv)
  def do_HEAD(self):
    """Handles HEAD request"""
    log("do_HEAD: rl="+str(self.requestline)+", head="+str(self.headers))
    super().do_HEAD()
  def readFrom(self,fn):
    """Read headers and data from given file"""
    hdrs = {}
    try:
      f = open(fn+".headers","tr")
      for l in f:
        if l[-1:]=="\n":
          l = l[:-1]
        i = l.find(": ")
        if -1!=i:
          hdrs[l[:i]] = l[i+2:]
      f.close()
    except (Exception,Error) as err:
      log("readFrom: header: error: "+str(err))
    try:
      f2 = open(fn,"br")
      data = f2.read()
      f2.close()
    except (Exception,Error) as err:
      log("readFrom: body: error: "+str(err))
    return (hdrs,data)
  def check(self,fn):
    log("check: "+fn)
    pair = None
    if os.access(fn, os.R_OK) and os.access(fn+".headers", os.R_OK):
      #os.access(fn+".status", os.R_OK):
      a = os.stat(fn)
      ct = time.time()
      ca = ct - a.st_ctime
      ma = ct - a.st_mtime
      log("check: createAge: "+str(ca)+", modAge: "+str(ma))
      # seven days of seconds
      sds = 7*24*60*60
      if a.st_ctime == a.st_mtime:
        # not modified file, use ctime
        t = a.st_ctime
        log("check: using ctime")
      else:
        # updated file, use mtime
        t = a.st_mtime
        log("check: using mtime")
      age = ct - t
      if age < sds:
        # created less than 7 days ago, use cache
        log("check: less than 7 days old: from cache")
        pair = self.readFrom(fn)
      else:
        # created more than 7 days ago, refresh
        log("check: older than 7 days: refreshing")
    else:
      log("check: header and body files not accessible")
    return pair
  def getFrom(self,conn,fn,printHeaders=False):
    """Sends HTTP GET request and reads response"""
    #log("getFrom: "+str(conn))
    conn.request(self.command,self.path,headers=self.headers)
    resp = conn.getresponse()
    log("getFrom: "+str(resp.status)+", "+str(resp.reason)+", "+str(resp.version))
    if "Content-Length" in resp.headers:
      cl = resp.headers["Content-Length"]
      log("getFrom: response length: "+cl)
      cl = int(cl)
    else:
      log("getFrom: no response length")
      cl = None
      printHeaders = True
    if printHeaders:
      for h in resp.headers:
        log("getFrom: resp.hdr: "+h+" = "+resp.headers[h])
    resp.debuglevel=1
    if None != cl:
      try:
        data = resp.read(cl)
      except (Exception,Error) as err:
        log("getFrom: read: error: "+str(err))
    else:
      data = resp.read()
    resp.debuglevel=0
    log("getFrom: "+str(len(data))+" bytes of response read")
    if "Transfer-encoding" in resp.headers:
      trenc = resp.headers["Transfer-encoding"]
      if "chunked"==trenc:
        log("getFrom: chunked -> fixed")
        del resp.headers["Transfer-encoding"]
        resp.headers["Content-Length"] = str(len(data))
    p = os.path.dirname(fn)
    os.makedirs(p,exist_ok=True)
    w2 = 0
    try:
      f2 = open(fn+".headers","t+w")
      for h in resp.headers:
        w2 += f2.write(h+": "+resp.headers[h]+"\n")
      f2.close()
    except (Exception,Error) as err:
      log("getFrom: header: error: "+str(err))
    log("getFrom: "+str(w2)+" bytes of headers written to file")
    try:
      f = open(fn,"b+w")
      w = f.write(data)
      f.close()
    except (Exception,Error) as err:
      log("getFrom: body: error: "+str(err))
    log("getFrom: "+str(w)+" bytes of body written to file")
    return (resp.headers,data)
  def handleJmmMedia(self,host):
    dir = "_jmm_"
    path = "/"+dir+self.path[4:]
    fn = self.cwd+path
    #log("handleJmmMedia: file: "+fn)
    pair = self.check(fn)
    if None != pair:
      (hdrs,data) = pair
    else:
      # not in cache, get it
      self.connectJmm(host)
      (hdrs,data) = self.getFrom(self.jmm,fn)
    self.respond(200,"Ok",hdrs,data)
  def handleJmmAdmin(self,host):
    dir = "_jmm_"
    path = "/"+dir+self.path[4:]
    log("handleJmmAdmin: fetching Admin")
    for h in self.headers:
      log("do_GET: req.hdr: "+h+" = "+self.headers[h])
    fn = self.cwd+path
    self.connectJmm(host)
    (hdrs,data) = self.getFrom(self.jmm,fn)
    self.respond(200,"Ok",hdrs,data)
  def handleAdbPic(self,host):
    dir = "_img7_"
    path = "/"+dir+self.path[5:]
    fn = self.cwd+path
    log("handleAdbPic: checking: "+fn)
    pair = self.check(fn)
    if None != pair:
      (hdrs,data) = pair
    else:
      # not in cache, get it
      self.connectImg7(host)
      (hdrs,data) = self.getFrom(self.img7,fn)
    self.respond(200,"Ok",hdrs,data)
  def handleTvdbPic(self,host):
    dir = "_tvdb_"
    path = "/"+dir+self.path
    fn = self.cwd+path
    log("handleTvdbPic: checking: "+fn)
    pair = self.check(fn)
    if None != pair:
      (hdrs,data) = pair
    else:
      # not in cache, get it
      self.connectTvdb(host)
      (hdrs,data) = self.getFrom(self.tvdb,fn)
    self.respond(200,"Ok",hdrs,data)
  def do_GET(self):
    """Handles GET request"""
    handled=False
    host = self.headers['Host']
    log("do_GET: path="+self.path+", proto="+self.request_version+", host="+host)
    if "jmm.azurewebsites.net"==host:
      if "/api/Media/"==self.path[:11] or "/api/CrossRef_"==self.path[:14]:
        self.handleJmmMedia(host)
        handled = True
      elif "/api/Admin"==self.path[:10] or "/api/animeidtitle/"==self.path[:18]:
        # not cacheable data, we do store it, but don't serve it from cache
        self.handleJmmAdmin(host)
        handled = True
      #else not handled
    elif "img7.anidb.net"==host:
      if "/pics/"==self.path[:6]:
        self.handleAdbPic(host)
        handled = True
      #else not handled
    elif "api.anidb.net:9001"==host:
      #for h in self.headers:
        #log("do_GET: in: "+h+" = "+self.headers[h])
      if "/httpapi?"==self.path[:9]:
        #expecting "request=anime&aid=<animeid>"
        args = self.path[9:]
        log("do_GET: args: "+args)
        args2 = args.split("&")
        #log("do_GET: args2: "+str(args2))
        isAniReq = ("request=anime" in args2)
        isMyListReq = ("request=mylist" in args2)
        aid=""
        for z in args2:
          if "aid="==z[:4]:
            aid=z[4:]
        fn = None
        if isAniReq and ""!=aid:
          dir = "_adb_"
          path = "/"+dir+"/anime/"+aid
          fn = self.cwd+path
        elif isMyListReq:
          dir = "_adb_"
          path = "/"+dir+"/mylist"
          fn = self.cwd+path
        if None != fn:
          log("do_GET: checking: "+fn)
          pair = self.check(fn)
          if None != pair:
            (hdrs,data) = pair
          else:
            # not in cache, get it
            self.connectAdb(host)
            (hdrs,data) = self.getFrom(self.adb,fn)
          self.respond(200,"Ok",hdrs,data)
          handled = True
        #else not "anime" and not "mylist" request
      #else not handled
    elif "thetvdb.com"==host:
      if "/banners/"==self.path[:9]:
        self.handleTvdbPic(host)
        handled = True
      #else not handled
    #else not handled
    if not handled:
      log("do_GET: let super handle: "+self.path)
      super().do_GET()
  def do_POST(self):
    """Handles POST request"""
    host = self.headers['Host']
    log("do_POST: path="+self.path+", proto="+self.request_version+", host="+host)
    if "jmm.azurewebsites.net"==host:
      #log("do_POST: "+host+" is JMM")
      #for h in self.headers:
        #log("do_POST: in: "+h+" = "+self.headers[h])
      if "Content-Length" in self.headers:
        cl = self.headers["Content-Length"]
        log("do_POST: inc data len: "+cl)
        cl = int(cl)
      else:
        log("do_POST: no req data len given")
        cl = None
      if None != cl:
        log("do_POST: reading req body of "+str(cl)+" bytes")
        data = self.rfile.read(cl)
      else:
        log("do_POST: reading all..")
        data = self.rfile.read()
      log("do_POST: read req "+str(len(data))+" bytes: "+str(data[:25]))
      self.connectJmm(host)
      resp = self.postTo(self.jmm,data)
      if "Content-Length" in resp.headers:
        cl = resp.headers["Content-Length"]
        log("do_POST: resp data len: "+cl)
        cl = int(cl)
      else:
        cl = None
        log("do_POST: no resp data len given")
      if None != cl:
        log("do_POST: reading resp body of "+str(cl)+" bytes")
        data = resp.read(cl)
      else:
        log("do_POST: reading all..")
        data = resp.read()
      log("do_POST: read resp "+str(len(data))+" bytes: "+str(data[:25]))
      self.send_response(resp.status,resp.reason)
      for h in resp.headers:
        #log("do_POST: out: "+h+" = "+resp.headers[h])
        self.send_header(h,resp.headers[h])
      self.end_headers()
      if 0 < len(data):
        d = self.wfile.write(data)
        log("do_POST: wrote resp of "+str(d)+" bytes")
      #log("do_POST: closing output stream")
      #self.wfile.close()
    else:
      self.send_error(404,"Not handling")
    #super().do_POST()
  def do_PUT(self):
    """Handles PUT request"""
    log("do_PUT: rl="+str(self.requestline)+", head="+str(self.headers))
    super.do_PUT()
  def do_DELETE(self):
    """Handles DELETE request"""
    log("do_DELETE: rl="+str(self.requestline)+", head="+str(self.headers))
    super.do_DELETE()
  def do_CONNECT(self):
    """Handles CONNECT request"""
    log("do_CONNECT: rl="+str(self.requestline))
    super.do_CONNECT()
  def do_OPTIONS(self):
    """Handles OPTIONS request"""
    log("do_OPTIONS: rl="+str(self.requestline))
    super.do_OPTIONS()
  def do_TRACE(self):
    """Handles TRACE request"""
    log("do_TRACE: rl="+str(self.requestline))
    super.do_TRACE()
  def do_PATCH(self):
    """Handles PATCH request"""
    log("do_PATCH: rl="+str(self.requestline))
    super.do_PATCH()
  def connectJmm(self,host):
    """Opens HTTP connection to JMM"""
    if None==self.jmm:
      log("connectJmm: "+host)
      self.jmm = http.client.HTTPConnection(host,timeout=30)
  def connectImg7(self,host):
    """Opens HTTP connection to anidb.net"""
    if None==self.img7:
      log("connectImg7: "+host)
      self.img7 = http.client.HTTPConnection(host,timeout=30)
  def connectAdb(self,host):
    """Opens HTTP connection to api.anidb.net"""
    if None==self.adb:
      log("connectAdb: "+host)
      self.adb = http.client.HTTPConnection(host,timeout=30)
  def connectTvdb(self,host):
    """Opens HTTP connection to thetvdb.com"""
    if None==self.tvdb:
      log("connectTvdb: "+host)
      self.tvdb = http.client.HTTPConnection(host,timeout=30)
  def postTo(self,conn,data):
    """Sends HTTP POST request and returns response object"""
    #log("postTo: "+str(conn))
    conn.request(self.command,self.path,data,self.headers)
    resp = conn.getresponse()
    log("postTo: "+str(resp.status)+", "+str(resp.reason)+", "+str(resp.version))
    return resp
  def respond(self,code,msg,hdrs,data):
    """Sends respond to client"""
    self.send_response(code,msg)
    for h in hdrs:
      #log("respond: out: "+h+" = "+hdrs[h])
      self.send_header(h,hdrs[h])
    self.end_headers()
    if 0<len(data):
      d = self.wfile.write(data)
      log("respond: sent "+(str(d))+" bytes of "+str(len(data)))
    #self.wfile.close()

class ThreadedHttpServer(socketserver.ThreadingMixIn,http.server.HTTPServer):
  pass

log("starting..")
handler_class = ProxyHandler

#httpd1 = http.server.HTTPServer(("",PROXY_PORT), handler_class)
httpd1 = ThreadedHttpServer(("",PROXY_PORT),handler_class)
t1 = threading.Thread(target=httpd1.serve_forever)
log("serving at port "+str(PROXY_PORT))
t1.start()

#httpd2 = http.server.HTTPServer(("",PROXY_PORT2), handler_class)
httpd2 = ThreadedHttpServer(("",PROXY_PORT2),handler_class)
t2 = threading.Thread(target=httpd2.serve_forever)
log("serving at port "+str(PROXY_PORT2))
t2.start()

httpd3 = ThreadedHttpServer(("",PROXY_PORT3),handler_class)
httpd3.socket = ssl.wrap_socket(httpd3.socket,server_side=True, \
 certfile='localhost.pem',ssl_version=ssl.PROTOCOL_TLSv1)
log("serving at port "+str(PROXY_PORT3))
httpd3.serve_forever()

#select_timeout=0.1
#while True:
#  r,w,e = select.select([httpd1,httpd2],[],[],select_timeout)
#  if httpd1 in r:
#    httpd1.handle_request()
#  if httpd2 in r:
#    httpd2.handle_request()

log("shutting down")
httpd2.shutdown()
httpd1.shutdown()
log("Done.")
