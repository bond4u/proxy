#!/usr/bin/env python3
#
# proxy EPISODE data cache test
#
import time
from EpisodeCache import EpisodeCache

def log(s):
  print(time.ctime()+" testEpiCache: "+s)

fn1 = "testepisodes1.txt"
log("creating epiCache1")
c = EpisodeCache(fn1)

k1 = "eid=149776"
log("getting epi1..")
d1 = c.get(k1)
if None == d1:
  log("getEpi1: "+str(d1)+" as expected")
else:
  log("getEpi1: "+str(d1)+" - not expected")

d1 = "240 EPISODE"+"\n"+"149776|9829|1|0|0|20|Cocoa Bean|||0|1"+"\n"
log("adding epi1..")
c.set(k1,d1)

log("getting epi1 again..")
d2 = c.get(k1)
if d1==d2:
  log("getEpi1 again: "+str(d2)+" as expected")
else:
  log("getEpi1 again: "+str(d2)+" - not expected")

log("saving cache..")
c.save()
log("save done, setting to None")
c = None
log("creating new epiCache")
c = EpisodeCache(fn1)
log("cached entries: "+str(c.data))
c.load()
log("cached entries again: "+str(len(c.data)))

d3 = c.get(k1)
if d1==d3:
  log("getEpi1 again2: "+str(d3)+" as expected")
else:
  log("getEpi1 again2: "+str(d3)+" - not expected")

k2 = "eid=149777&s=TgG9f"
d4 = c.get(k2)
if None==d4:
  log("getEpi2: "+str(d4)+" as expected")
else:
  log("getEpi2: "+str(d4)+" - not expected")

d4 = "240 EPISODE"+"\n"+"149777|9829|1|0|0|19|Fava Bean|||0|1"+"\n"
c.set(k2,d4,True)

c = None
c = EpisodeCache(fn1)
c.load()
log("cached entries again2: "+str(len(c.data)))

d5 = c.get(k2)
if d4==d5:
  log("getEpi3: "+str(d5)+" as expected")
else:
  log("getEpi3: "+str(d5)+" - not expected")
