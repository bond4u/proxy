#!/usr/bin/env python3
#
# proxy CALENDAR data cache
#
import time

def log(s):
  print(time.ctime()+" CalCache: "+s)

class CalCache():
  '''Calendar data caching'''
  def __init__(self,fn):
    '''Sets up calendar cache'''
    self.fileName = fn
    self.lines = []
    self.idate = None
    self.udate = None
  def parse(self,data):
    '''Parses a line(s), from server or from file'''
    line = None
    idate = None
    udate = None
    if (None != data) and (0 < len(data)):
      i = data.find("\n")
      if -1 != i:
        line = data[0:i]
        data = data[i+1:]
        #log("parse: multi: line: "+line)
      else:
        line = data
        data = None
        #log("parse: single: line: "+line)
      j = line.find(" ")
      if -1 != j:
        # first is code then keyword then args
        k = line.find(" ",j+1)
        if -1 != k:
          args = line[k+1:]
          line = line[0:k]
          #log("parse: args: "+args)
          vals = args.split("&")
          for pair in vals:
            #log("parse: pair: "+pair)
            if "idate=" == pair[0:6]:
              v = pair[6:]
              if "" != v:
                idate = float(v)
            elif "udate=" == pair[0:6]:
              v = pair[6:]
              if "" != v:
                udate = float(v)
        #else no args
      #else no cmd
    log("parse: return L: '"+str(line)+"' D: '"+str(data)+"'")
    return (line,data,idate,udate)
  def load(self):
    '''Loads calendar info from file'''
    self.lines = []
    try:
      inf = open(self.fileName,"r")
      for line in inf:
        l = len(line)
        if (0 < l) and ("\n"==line[l-1:]):
          #log("trimming newline '"+line[l-1:]+"'")
          line = line[0:l-1]
        #log("load line: "+line)
        if 0 == len(self.lines):
          # first line
          (line,data,idate,udate) = self.parse(line)
          if None == idate:
            idate = time.time()
          self.idate = idate
          self.udate = udate
        #else followup lines
        if 0 < len(line):
          self.lines.append(line)
      inf.close()
    except FileNotFoundError:
      pass
    log("load: data from file: "+str(len(self.lines)))
  def save(self):
    '''Saves calendar data to file'''
    ouf = open(self.fileName,"w")
    first = True
    for line in self.lines:
      if first:
        first = False
        line += " idate="
        if None != self.idate:
          line += str(self.idate)
        line += "&udate="
        if None != self.udate:
          line += str(self.udate)
      #else followup line
      #log("save line: '"+line+"'")
      if 0 < len(line):
        ouf.write(line+"\n")
    ouf.close()
    log("save: data to file: "+str(len(self.lines)))
  def get(self):
    '''Returns cached calendar'''
    r = None
    #log("get: self.lines: "+str(self.lines))
    if 0 < len(self.lines):
      r = ""
      #log("get: iterating lines")
      for line in self.lines:
        r += line+"\n"
    #log("get: returning '"+str(r)+"'")
    return r
  def set(self,data,append=False):
    '''Sets calendar data in cache, optionally writes to file'''
    if None == self.idate:
      self.idate = time.time()
    else:
      self.udate = time.time()
    self.lines = []
    (line,data,idate,udate) = self.parse(data)
    while (None != line) and ("" != line):
      self.lines.append(line)
      (line,data,idate,udate) = self.parse(data)
    #log("setCal: lines: "+str(len(self.lines)))
    if append:
      # not really an append, overwrite
      self.save()
  def getDates(self):
    '''Returns calendar idate and udate'''
    return (self.idate,self.udate)
