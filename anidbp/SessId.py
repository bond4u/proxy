#!/usr/bin/env python3
#
# Session IDs
#
import time
import random

def log(s):
  print(time.ctime()+" SessId: "+s)

# remember generated session id's
global g_sids
g_sids = []

def genSid():
  '''Generate 5-letter session id'''
  global g_sids
  # 3 ranges of chars
  o = [ ord('0'), ord('9'), ord('A'), ord('Z'), ord('a'), ord('z') ]
  d1 = o[1]-o[0]+1
  d2 = o[3]-o[2]+1
  d3 = o[5]-o[4]+1
  t = d1 + d2 + d3
  while True:
    s = ""
    for i in range(5):
      r = random.randint(0,t-1)
      c = chr(o[0]+r)
      if c > '9':
        r -= d1
      c = chr(o[2]+r)
      if c > 'Z':
        r -= d2
      c = chr(o[4]+r)
      s += c
    if not s in g_sids:
      break
  g_sids.append(s)
  return s

def removeSess(s):
  r = ""
  while 0 < len(s):
    i = s.find("&")
    #log("removeSess: i: "+str(i))
    if -1 != i:
      pair = s[0:i]
      s = s[i+1:]
    else:
      pair = s
      s = ""
    #log("removeSess: pair: "+pair)
    if ("s=" != pair[0:2]) and ("enc=" != pair[0:4]):
      if 0 < len(r):
        r += "&"
      r += pair
  log("removeSess: result: "+r)
  return r
