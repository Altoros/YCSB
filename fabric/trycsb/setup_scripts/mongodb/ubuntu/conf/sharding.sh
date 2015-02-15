#!/bin/sh

if [ -z "$1" ]; then
    echo "Host address required"
    exit 1
fi

CURRENT_HOST_ADDR=$1


echo "setup config servers"
mkdir -p /disk1/mongodb-data/db/config
mongod --configsvr --dbpath /disk1/mongodb-data/db/config --port 57000 --fork --logpath /disk1/mongodb-logs/config.log
echo "waiting for a replica set to come online"
sleep 60

echo "starting mongos"
mongos --configdb 50.97.182.67:57000,50.97.182.68:57000,50.97.182.69:57000 --fork --logpath /disk1/mongodb-logs/mongos.log
