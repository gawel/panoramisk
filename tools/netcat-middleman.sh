#!/bin/bash

host=localhost
port=5039
if [ "$1" != "" ]; then
    host=$1
    port=5038
fi;

while true
do
    BACKUP_EXT=$(date +%y%m%d%h%m%s)
    if [[ -f outgoing.log ]]; then
        cp outgoing.log outgoing.log.$BACKUP_EXT
    fi
    if [[ -f incoming.log ]]; then
        cp incoming.log incoming.log.$BACKUP_EXT
    fi
    rm pipe
    mkfifo pipe
    echo "Listening on localhost:$port"
    echo "Capture incoming and outgoing traffic from $host:5038"
    nc -l -p $port < pipe | tee outgoing.log | nc $host 5038 | tee pipe incoming.log
done
