#!/bin/bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9300 > /tmp/chrome9300.log 2>&1 &
echo "Chrome started with pid $!"
