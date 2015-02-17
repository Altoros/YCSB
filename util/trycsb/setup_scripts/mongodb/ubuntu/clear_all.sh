#!/bin/sh

echo "killing mongod and mongos"
killall mongod
killall monogs

echo "removing data and log files"
rm -rf /disk1/mongodb-data/db/
rm -rf /disk1/mongodb-logs/

echo "creating data and log folder"
mkdir -p /disk1/mongodb-data/db/
mkdir -p /disk1/mongodb-logs/

