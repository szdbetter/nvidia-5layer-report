#!/bin/bash
nohup npx serve rdw_dashboard -l 3000 > serve.log 2>&1 &
echo $! > serve.pid
nohup npx localtunnel --port 3000 > lt.log 2>&1 &
echo $! > lt.pid
sleep 3
cat lt.log
