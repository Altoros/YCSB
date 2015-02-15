#!/bin/sh
echo "prepare a replica set on a shard1"
mkdir -p /disk1/mongodb-data/db/shard0/rs0
mkdir -p /disk1/mongodb-data/db/shard1/rs0
mongod --shardsvr --dbpath /disk1/mongodb-data/db/shard0/rs0 --port 27000 --fork --replSet shard0 --logpath /disk1/mongodb-logs/shard0-rs0.log
mongod --shardsvr --dbpath /disk1/mongodb-data/db/shard1/rs0 --port 37000 --fork --replSet shard1 --logpath /disk1/mongodb-logs/shard1-rs0.log

sleep 10

mongo --port 37000 << 'EOF'
config = { _id : "shard1",
            members : [{ _id : 0, host : "50.97.182.68:37000"},
                       { _id : 1, host : "50.97.182.69:37000"}]
         };
rs.initiate(config)
EOF