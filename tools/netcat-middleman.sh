#!/bin/bash
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
    echo "Capture incoming and outgoing traffic:"
    nc -l -p 5039 < pipe | tee outgoing.log | nc localhost 5038 | tee pipe incoming.log
done
