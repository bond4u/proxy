#!/bin/tcsh

set D=`date +%Y-%m-%d_%H-%M-%S`
#echo $D
nohup ./httpp.py |& tee logs/proxy-${D}.log
