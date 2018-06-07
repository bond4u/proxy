#!/usr/bin/env python3
#
# proxy EPISODE data cache
#
import time

def log(s):
  print(time.ctime()+" EpiCache: "+s)

class EpisodeCache():
  '''EPISODE data caching'''
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
    log("parse: return K: "+key+" V: "+line)
    return (key,line,idate,udate)
  def load(self):
    '''Loads EPISODE info from file'''
    try:
      inf = open(self.fileName,"r")
      lastReq = ""
      for line in inf:
        l = len(line)
        if (0 < l) and ("\n"==line[l-1:]):
          #log("trimming newline '"+line[l-1:]+"'")
          line = line[0:l-1]
        (req,resp,idate,udate) = self.parse(line)
        if None == idate:
          idate = time.time()
        if ("" != req) and ("" != resp):
          resp += "\n"
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
    '''Saves EPISODE info to file'''
    ouf = open(self.fileName,"w")
    for key in self.data:
      log("save: entry: "+str(key))
      val = self.data[key]
      data = val["DATA"]
      idate = val["IDATE"]
      udate = val["UDATE"]
      if None == udate:
        udate = ""
      values = "idate="+str(idate)+"&udate="+str(udate)+"&"+data
      ouf.write(key+"&"+values+"\n")
    ouf.close()
    log("save: data to file: "+str(len(self.data)))
  def get(self,key):
    '''Returns cached EPISODE'''
    (req,resp,idate,udate) = self.parse(key)
    r = None
    if req in self.data:
      val = self.data[req]
      r = val["DATA"]
    return r
  def set(self,key,data,append=False):
    '''Add EPISODE request and response to cache'''
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
      outf = open(self.fileName,"a")
      if None == udate:
        udate = ""
      values = "idate="+str(idate)+"&udate="+str(udate)+"&"+data
      outf.write(req+"&"+values+"\n")
      outf.close()
  def getDates(self,key):
    '''Returns EPISODE idate and udate'''
    idate = None
    udate = None
    (req,resp,idate,udate) = self.parse(key)
    if req in self.data:
      val = self.data[req]
      idate = val["IDATE"]
      udate = val["UDATE"]
    return (idate,udate)
