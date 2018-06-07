#!/usr/bin/env python3
#
# proxy MYLISTADD data cache test
#
import time
from MyListCache import MyListCache

def log(s):
  print(time.ctime()+" testMyListCache: "+s)

fn1 = "testmylist1.txt"
log("creating MyListCache1")
c = MyListCache(fn1)

k1 = "size=487159568&ed2k=861C7384D37E6AA155734CB77FE50270&viewed=0&state=2"
log("getting myList1..")
d1 = c.get(k1)
if None == d1:
  log("getMyList1: "+str(d1)+" as expected")
else:
  log("getMyList1: "+str(d1)+" - not expected")

d1 = "210 MYLIST ENTRY ADDED"+"\n"+"248427482"+"\n"
log("adding myList1..")
c.set(k1,d1)

log("getting myList1 again..")
d2 = c.get(k1)
if d1==d2:
  log("getMyList1 again: "+str(d2)+" as expected")
else:
  log("getMyList1 again: "+str(d2)+" - not expected")

log("saving cache..")
c.save()
log("save done, setting to None")
c = None
log("creating new myListCache")
c = MyListCache(fn1)
log("cached entries: "+str(c.data))
c.load()
log("cached entries again: "+str(len(c.data)))

d3 = c.get(k1)
if d1==d3:
  log("getMyList1 again2: "+str(d3)+" as expected")
else:
  log("getMyList1 again2: "+str(d3)+" - not expected")

k2 = "size=1375035134&ed2k=505433F2DB67DAD75C89F35FB19FB5BD&viewed=0&state=2&s=TgG9f"
d4 = c.get(k2)
if None==d4:
  log("getMyList2: "+str(d4)+" as expected")
else:
  log("getMyList2: "+str(d4)+" - not expected")

d4 = "310 FILE ALREADY IN MYLIST"+"\n"+"204064714|918002|64812|4817|0|1439189416|2|0||||0"+"\n"
c.set(k2,d4,True)

c = None
c = MyListCache(fn1)
c.load()
log("cached entries again2: "+str(len(c.data)))

d5 = c.get(k2)
if d4==d5:
  log("getMyList3: "+str(d5)+" as expected")
else:
  log("getMyList3: "+str(d5)+" - not expected")
