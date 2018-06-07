#!/usr/bin/env python3
#
# proxy FILE data cache
#
import time

def log(s,fallback=True):
  try:
    print(time.ctime()+" FileCache: "+s,flush=True)
  except (TypeError,UnicodeError,UnicodeEncodeError,UnicodeDecodeError) as err:
    if not fallback:
      raise err
    z = bytes(s,"utf-8")
    print(time.ctime()+" FileCache: "+str(z),flush=True)

class FileCache():
  '''FILE data caching'''
  def __init__(self,fn):
    '''Sets up cache'''
    self.fileName = fn
    self.files = {}
    #self.load()
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
          if "" == s:
            idate = None
          else:
            idate = float(s)
        elif "udate=" == pair[0:6]:
          s = pair[6:]
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
        if "s=" != line[0:2]:
          if 0 < len(key):
            key += "&"
          key += line
        #else just ignore "s=" pair
        line = ""
      else: # no pair, just data
        #log("parse: end: "+line)
        break
    log("parse: return K: "+str(key)+" V: "+str(line))
    return (key,line,idate,udate)
  def load(self):
    '''Loads file info from file'''
    try:
      inf = open(self.fileName,"br")
      for line in inf:
        try:
          line = line.decode("utf-8")
        except UnicodeError as err:
          log("load: unicode error: "+str(err)+" on line: "+str(line))
        l = len(line)
        if (0 < l) and ("\n"==line[l-1:]):
          #log("trimming newline '"+line[l-1:]+"'")
          line = line[0:l-1]
        (req,resp,idate,udate) = self.parse(line)
        if None == idate:
          idate = time.time()
        self.files[req] = { "DATA": resp, "IDATE": idate, "UDATE": udate }
      inf.close()
    except FileNotFoundError:
      pass
    log("load: file data: "+str(len(self.files)))
  def save(self):
    '''Saves file info to file'''
    try:
      ouf = open(self.fileName,"bw")
      for key in self.files:
        #log("save: entry: "+str(e))
        val = self.files[key]
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
    except UnicodeError as err:
      log("save: unicode error: "+str(err))
    log("save: file data: "+str(len(self.files)))
  def getFile(self,data):
    '''Returns cached file'''
    (req,resp,idate,udate) = self.parse(data)
    r = None
    if req in self.files:
      val = self.files[req]
      r = val["DATA"]
    return r
  def addFile(self,key,data,append=False):
    '''Add file request and response to cache'''
    (req,resp,idate,udate) = self.parse(key)
    log("addFile: '"+str(req)+"', '"+str(resp)+"', '"+str(idate)+"', '"+str(udate)+"'")
    if req in self.files:
      append = False # known entry, writing it to file will create duplicate
      val = self.files[req]
      idate = val["IDATE"]
      udate = time.time()
    else:
      idate = time.time()
      udate = None
    self.files[req] = { "DATA": data, "IDATE": idate, "UDATE": udate }
    if append:
      outf = open(self.fileName,"ba")
      if None == udate:
        udate = ""
      values = "idate="+str(idate)+"&udate="+str(udate)+"&"+data
      val = req+"&"+values+"\n"
      val = bytes(val,"utf-8")
      outf.write(val)
      outf.close()
  def getFileDates(self,req):
    '''Returns file idate and udate'''
    idate = None
    udate = None
    if req in self.files:
      val = self.files[req]
      idate = val["IDATE"]
      udate = val["UDATE"]
    return (idate,udate)
