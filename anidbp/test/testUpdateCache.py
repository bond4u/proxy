#!/usr/bin/env python3
#
# proxy UPDATED cache test
#
import time
from UpdateCache import UpdateCache

def log(s):
  print(time.ctime()+" testUpdateCache: "+s)

fn1 = "testupdated1.txt"
log("creating updateCache1")
c = UpdateCache(fn1)

f1 = "entity=1&time=1519768249&s=izqAz"
d1 = "243 UPDATED\n"
log("getting updates1..")
d2 = c.get(f1)
if d1 == d2:
  log("getUpdate1: "+str(d2)+" as expected")
else:
  log("getUpdate1: "+str(d2)+" - not expected")

d3 = "243 UPDATED"+"\n"+"1|1|150243234|5432543,254325,432543"
log("adding updates1..")
c.set(f1,d3)

log("getting file1 again..")
d4 = c.get(f1)
if d3==d4:
  log("getUpdate1 again: "+str(d4)+" as expected")
else:
  log("getUpdate1 again: "+str(d4)+" - not expected")

log("saving updateCache..")
c.save()
log("save done, setting to None")
c = None
log("creating new updateCache")
c = UpdateCache(fn1)
log("cached entries: "+str(c.data))
c.load()
log("cached entries again: "+str(len(c.data)))

d5 = c.get(f1)
if d3==d5:
  log("getUpdate1 again2: "+str(d5)+" as expected")
else:
  log("getUpdate1 again2: "+str(d5)+" - not expected")

f2 = "entity=1&time=1520027449&s=9gYSj"
d6 = c.get(f2)
if d3==d6:
  log("getFile2: "+str(d6)+" as expected")
else:
  log("getFile2: "+str(d6)+" - not expected")

d5 = "243 UPDATED"+"\n"+"1|11|1520502739|8211,13785,11909,13377,13421,13069,13500,6064,13054,2674,1236"
c.set(f2,d5,True)

c = None
c = UpdateCache(fn1)
c.load()
log("cached entries again2: "+str(len(c.data)))
