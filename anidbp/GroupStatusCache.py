#!/usr/bin/env python3
#
# proxy GROUPSTATUS data cache
#
import time

def log(s,fallback=True):
  try:
    print(time.ctime()+" GrStaCache: "+s,flush=True)
  except (TypeError,UnicodeError,UnicodeEncodeError,UnicodeDecodeError) as err:
    if not fallback:
      raise err
    z = bytes(s,"utf-8")
    print(time.ctime()+" GrStaCache: "+str(z),flush=True)

class GroupStatusCache():
  '''GROUPSTATUS data caching'''
  def __init__(self,fn):
    '''Sets up cache'''
    self.fileName = fn
    self.data = {}
  def parse(self,line):
    '''Parses a line, from server or from file'''
    key = ""
    idate = None
    udate = None
    while 0 < len(line):
      i = line.find("&")
      j = line.find("=")
      k = line.find("|") # data/value part
      #log("parse: i: "+str(i)+" j: "+str(j)+" k: "+str(k))
      if (-1 != i) and (-1 != j) and (-1 == k or i < k):
        pair = line[0:i]
        #log("parse: pair: "+pair)
        line = line[i+1:]
        if "s=" == pair[0:2]:
          #log("parse: ignoring: "+pair)
          pass
        elif "idate=" == pair[0:6]:
          s = pair[6:]
          #log("parse: idate: "+str(s))
          if "" == s:
            idate = None
          else:
            idate = float(s)
        elif "udate=" == pair[0:6]:
          s = pair[6:]
          #log("parse: udate: "+str(s))
          if "" == s:
            udate = None
          else:
            udate = float(s)
        else:
          if 0 < len(key):
            key += "&" # separator
          key += pair
      elif (-1 == i) and (-1 != j):
        #log("parse: last pair: "+line)
        if "s=" != line[:2]:
          if 0 < len(key):
            key += "&"
          key += line
        #else just ignore "s=" pair
        line = ""
      else: # no pair, just data
        #log("parse: end: "+line)
        break
    log("parse: return K: "+key+" V: "+line)
    return (key,line,idate,udate)
  def load(self):
    '''Loads GROUPSTATUS info from file'''
    try:
      inf = open(self.fileName,"br")
      lastReq = ""
      for line in inf:
        line = line.decode("utf-8")
        l = len(line)
        if (0 < l) and ("\n"==line[l-1:]):
          #log("trimming newline '"+line[l-1:]+"'")
          line = line[0:l-1]
        (req,resp,idate,udate) = self.parse(line)
        if None == idate:
          idate = time.time()
        if ("" != req) and ("" != resp):
          resp += "\n"
          #log("load: idate: "+str(idate)+" udate: "+str(udate)+" resp: "+resp)
          self.data[req] = { "DATA": resp, "IDATE": idate, "UDATE": udate }
          lastReq = req
        elif ("" == req) and ("" != resp) and ("" != lastReq):
          d = self.data[lastReq]
          resp += "\n"
          d["DATA"] += resp
        else:
          #log("load: out of data to parse")
          lastReq = ""
      inf.close()
    except FileNotFoundError:
      pass
    log("load: data from file: "+str(len(self.data)))
  def save(self):
    '''Saves GROUPSTATUS info to file'''
    ouf = open(self.fileName,"bw")
    for key in self.data:
      log("save: entry: "+str(key))
      val = self.data[key]
      data = val["DATA"]
      idate = val["IDATE"]
      udate = val["UDATE"]
      if None == udate:
        udate = ""
      values = "idate="+str(idate)+"&udate="+str(udate)+"&"+data
      val = key+"&"+values+"\n"
      val = bytes(val,"utf-8")
      ouf.write(val)
    ouf.close()
    log("save: data to file: "+str(len(self.data)))
  def get(self,key):
    '''Returns cached GROUPSTATUS'''
    (req,resp,idate,udate) = self.parse(key)
    r = None
    if req in self.data:
      val = self.data[req]
      r = val["DATA"]
    return r
  def set(self,key,data,append=False):
    '''Add GROUPSTATUS request and response to cache'''
    (req,resp,idate,udate) = self.parse(key)
    if req in self.data:
      append = False # known entry, writing it to file will create duplicate
      val = self.data[req]
      idate = val["IDATE"]
      udate = time.time()
    else:
      idate = time.time()
      udate = None
    self.data[req] = { "DATA": data, "IDATE": idate, "UDATE": udate }
    if append:
      outf = open(self.fileName,"ba")
      if None == udate:
        udate = ""
      values = "idate="+str(idate)+"&udate="+str(udate)+"&"+data
      val = req+"&"+values+"\n"
      val = bytes(val,"utf-8")
      outf.write(val)
      outf.close()
  def getDates(self,key):
    '''Returns GROUPSTATUS idate and udate'''
    idate = None
    udate = None
    (req,resp,idate,udate) = self.parse(key)
    if req in self.data:
      val = self.data[req]
      idate = val["IDATE"]
      udate = val["UDATE"]
    return (idate,udate)
