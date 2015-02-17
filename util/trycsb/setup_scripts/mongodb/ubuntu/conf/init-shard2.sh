#!/bin/sh
echo "prepare a replica set on a shard1"
mkdir -p /disk1/mongodb-data/db/shard1/rs0
mkdir -p /disk1/mongodb-data/db/shard2/rs0
mongod --shardsvr --dbpath /disk1/mongodb-data/db/shard1/rs0 --port 37000 --fork --replSet shard1 --logpath /disk1/mongodb-logs/shard1-rs0.log
mongod --shardsvr --dbpath /disk1/mongodb-data/db/shard2/rs0 --port 27000 --fork --replSet shard2 --logpath /disk1/mongodb-logs/shard2-rs0.log

sleep 10

mongo --port 27000 << 'EOF'
config = { _id : "shard2",
            members : [{ _id : 0, host : "50.97.182.69:27000"},
                       { _id : 1, host : "50.97.182.67:37000"}]
         };
rs.initiate(config)
EOF