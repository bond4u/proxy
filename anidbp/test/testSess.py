#!/usr/bin/env python3

import time
import SessId

def log(s):
  print(time.ctime()+" sess: "+s)

sid = SessId.genSid()
log("sid: "+sid)

s = "one=two&three=four&s=five"
z = SessId.removeSess(s)
log("str: "+s+" cleaned: "+z)
