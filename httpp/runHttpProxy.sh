#!/bin/tcsh

set D=`date +%Y-%m-%d_%H-%M-%S`
#echo $D
nohup ./httpp.py >& logs/proxy-${D}.log
