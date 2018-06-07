#!/usr/bin/env python3
#
# proxy UPDATED data cache
#
import time

def log(s):
  print(time.ctime()+" UpdateCache: "+s)

class UpdateCache():
  '''UPDATED data caching'''
  def __init__(self,fn):
    '''Sets up cache'''
    self.fileName = fn
    self.data = None
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
    '''Loads UPDATED info from file'''
    try:
      inf = open(self.fileName,"r")
      for line in inf:
        l = len(line)
        if (0 < l) and ("\n"==line[l-1:]):
          #log("trimming newline '"+line[l-1:]+"'")
          line = line[0:l-1]
        (req,resp,idate,udate) = self.parse(line)
        if None == idate:
          idate = time.time()
        self.data = { "KEY": req, "DATA": resp, "IDATE": idate, "UDATE": udate }
        break
      inf.close()
    except FileNotFoundError:
      pass
    c = 0 if None==self.data else len(self.data)
    log("load: data from file: "+str(c))
  def save(self):
    '''Saves UPDATED info to file'''
    ouf = open(self.fileName,"w")
    if None != self.data:
      key = self.data["KEY"]
      #log("save: entry: "+str(self.data))
      data = self.data["DATA"]
      idate = self.data["IDATE"]
      udate = self.data["UDATE"]
      if None == udate:
        udate = ""
      values = "idate="+str(idate)+"&udate="+str(udate)+"&"+data
      ouf.write(key+"&"+values+"\n")
    ouf.close()
    log("save: data to file: "+str(len(self.data)))
  def get(self,data):
    '''Returns cached UPDATED'''
    (req,resp,idate,udate) = self.parse(data)
    r = None
    if None != self.data:
      r = self.data["DATA"]
    return r
  def set(self,key,data,append=False):
    '''Add UPDATED request and response to cache'''
    (req,resp,idate,udate) = self.parse(key)
    if None != self.data:
      idate = self.data["IDATE"]
      udate = time.time()
    else:
      idate = time.time()
      udate = None
    self.data = { "KEY": req, "DATA": data, "IDATE": idate, "UDATE": udate }
    if append:
      self.save()
  def getDates(self):
    '''Returns UPDATED idate and udate'''
    idate = None
    udate = None
    if None != self.data:
      idate = self.data["IDATE"]
      udate = self.data["UDATE"]
    return (idate,udate)
