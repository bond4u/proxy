#!/usr/bin/env python3
#
# proxy MYLISTSTATS data cache test
#
import time
from MyListStatsCache import MyListStatsCache

def log(s):
  print(time.ctime()+" testMyLSCache: "+s)

fn1 = "testmyliststats1.txt"
log("creating grMyLSCache1")
c = MyListStatsCache(fn1)

log("getting myLS1..")
d1 = c.get()
if None == d1:
  log("getMyLS1: "+str(d1)+" as expected")
else:
  log("getMyLS1: "+str(d1)+" - not expected")

d1 = "222 MYLIST STATS"+"\n"+"3478|33479|47561|8958186|0|0|0|0|100|0|0|19|0|67|31|0|2034"+"\n"
log("adding myLS1..")
c.set(d1)

log("getting myLS1 again..")
d2 = c.get()
if d1==d2:
  log("getMyLS1 again: "+str(d2)+" as expected")
else:
  log("getMyLS1 again: "+str(d2)+" - not expected")

log("saving cache..")
c.save()
log("save done, setting to None")
c = None
log("creating new grStaCache")
c = MyListStatsCache(fn1)
log("cached entries: "+str(c.data))
c.load()
log("cached entries again: "+str(len(c.data)))

d3 = c.get()
if d1==d3:
  log("getMyLS1 again2: "+str(d3)+" as expected")
else:
  log("getMyLS1 again2: "+str(d3)+" - not expected")

d4 = "222 MYLIST STATS"+"\n"+"3478|33479|47561|8958186|0|0|0|0|100|0|0|19|0|67|31|0|2034"+"\n"
c.set(d4,True)

c = None
c = MyListStatsCache(fn1)
c.load()
log("cached entries again2: "+str(len(c.data)))

d5 = c.get()
if d4==d5:
  log("getMyLS3: "+str(d5)+" as expected")
else:
  log("getMyLS3: "+str(d5)+" - not expected")
