#!/usr/bin/env python3
#
# proxy GROUPSTATUS data cache test
#
import time
from GroupStatusCache import GroupStatusCache

def log(s):
  print(time.ctime()+" testGrStaCache: "+s)

fn1 = "testgroupstatus1.txt"
log("creating grStaCache1")
c = GroupStatusCache(fn1)

k1 = "aid=7400"
log("getting grSta1..")
d1 = c.get(k1)
if None == d1:
  log("getGrSta1: "+str(d1)+" as expected")
else:
  log("getGrSta1: "+str(d1)+" - not expected")

d1 = "225 GROUPSTATUS"+"\n"+"670|Anime-Supreme|3|12|0|0|1-12"+"\n"
log("adding grSta1..")
c.set(k1,d1)

log("getting grSta1 again..")
d2 = c.get(k1)
if d1==d2:
  log("getGrSta1 again: "+str(d2)+" as expected")
else:
  log("getGrSta1 again: "+str(d2)+" - not expected")

log("saving cache..")
c.save()
log("save done, setting to None")
c = None
log("creating new grStaCache")
c = GroupStatusCache(fn1)
log("cached entries: "+str(c.data))
c.load()
log("cached entries again: "+str(len(c.data)))

d3 = c.get(k1)
if d1==d3:
  log("getGrSta1 again2: "+str(d3)+" as expected")
else:
  log("getGrSta1 again2: "+str(d3)+" - not expected")

k2 = "aid=1503&s=TgG9f"
d4 = c.get(k2)
if None==d4:
  log("getGrSta2: "+str(d4)+" as expected")
else:
  log("getGrSta2: "+str(d4)+" - not expected")

d4 = "225 GROUPSTATUS"+"\n"+"79|Ripping Gods|3|4|0|0|1-4"+"\n"
d4 += "1270|Anime No Sekai|3|4|375|4|1-4"+"\n"+"149777|9829|1|0|0|19|Fava Bean|||0|1"+"\n"
c.set(k2,d4,True)

c = None
c = GroupStatusCache(fn1)
c.load()
log("cached entries again2: "+str(len(c.data)))

d5 = c.get(k2)
if d4==d5:
  log("getGrSta3: "+str(d5)+" as expected")
else:
  log("getGrSta3: "+str(d5)+" - not expected")
