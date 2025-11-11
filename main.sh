#!/bin/sh

export DISPLAY=${DISPLAY:-:0}

while true; do
  sleep 10
  python3 foos.py
done

