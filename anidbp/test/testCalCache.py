#!/usr/bin/env python3
#
# proxy calendar data cache test
#
import time
from CalCache import CalCache

def log(s):
  print(time.ctime()+" testCalCache: "+s)

fn1 = "testcal1.txt"
log("creating calCache1")
c = CalCache(fn1)

log("getting file1..")
d1 = c.get()
if None == d1:
  log("getCal1: "+str(d1)+" as expected")
else:
  log("getCal1: "+str(d1)+" - not expected")

d1 = "297 CALENDAR"+"\n"
log("setting calendar1..")
c.set(d1)

log("getting calendar1 again..")
d2 = c.get()
if d1==d2:
  log("getCal1 again: "+str(d2)+" as expected")
else:
  log("getCal1 again: "+str(d2)+" - not expected")

log("saving cache..")
c.save()
log("save done, setting to None")
c = None
log("creating new CalCache")
c = CalCache(fn1)
log("cached calendar: "+str(len(c.lines)))
c.load()
log("loaded calendar again: "+str(len(c.lines)))

d3 = c.get()
if d1==d3:
  log("getCal1 again2: "+str(d3)+" as expected")
else:
  log("getCal1 again2: "+str(d3)+" - not expected")

d5 = "297 CALENDAR"+"\n"+"13773|1517702400|0"+"\n"
log("appending..")
c.set(d5,True)
log("setting to None")
c = None
log("re-creating..")
c = CalCache(fn1)
log("loading again..")
c.load()
log("cached entries again2: "+str(len(c.lines)))
