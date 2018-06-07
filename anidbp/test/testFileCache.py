#!/usr/bin/env python3
#
# proxy data cache test
#
import time
from FileCache import FileCache

def log(s):
  print(time.ctime()+" testFileCache: "+s)

fn1 = "testfiles1.txt"
log("creating fileCache1")
c = FileCache(fn1)

f1 = "size=8429&ed2k=C2FAD4A41C26FD8840A72350C9A10A47&fmask=7FF8FFF9FE&amask=0000FCC0"
log("getting file1..")
d1 = c.getFile(f1)
if None == d1:
  log("getFile1: "+str(d1)+" as expected")
else:
  log("getFile1: "+str(d1)+" - not expected")

d1 = "test|data|not|important & confusing"
log("adding file1..")
c.addFile(f1,d1)

log("getting file1 again..")
d2 = c.getFile(f1)
if d1==d2:
  log("getFile1 again: "+str(d2)+" as expected")
else:
  log("getFile1 again: "+str(d2)+" - not expected")

log("saving cache..")
c.save()
log("save done, setting to None")
c = None
log("creating new fileCache")
c = FileCache(fn1)
log("cached entries: "+str(len(c.files)))
c.load()
log("cached entries again: "+str(len(c.files)))

d3 = c.getFile(f1)
if d1==d3:
  log("getFile1 again2: "+str(d3)+" as expected")
else:
  log("getFile1 again2: "+str(d3)+" - not expected")

f2 = "size=195290750&ed2k=B1E8BDDF19656086F289079DFA53ABFD&fmask=7FF8FFF9FE&amask=0000FCC0&s=JIDFx"
d4 = c.getFile(f2)
if None==d4:
  log("getFile2: "+str(d4)+" as expected")
else:
  log("getFile2: "+str(d4)+" - not expected")

d5 = "another|test|data|not|confusing & important|again|blah"
c.addFile(f2,d5,True)

c = None
c = FileCache(fn1)
c.load()
log("cached entries again2: "+str(len(c.files)))
