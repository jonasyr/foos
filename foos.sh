#!/bin/sh

cd `dirname $0`
export DISPLAY=${DISPLAY:-:0}
exec ./foos.py
