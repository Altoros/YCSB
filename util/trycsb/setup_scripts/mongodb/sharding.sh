#!/bin/sh

echo "killing mongod and mongos"
killall mongod
killall monogs
echo "removing data files"
rm -rf /disk1/data/db/

echo "creating data folder"
mkdir -p /disk1/data/db/
chown `id -u` /disk1/data/db

echo "start a replica set on a shard0"
mkdir -p /disk1/data/db/shard0/rs0 /disk1/data/db/shard0/rs1
mongod --shardsvr --dbpath /disk1/data/db/shard0/rs0 --port 27000 --fork --replSet shard0 --logpath /disk1/logs/shard0-rs0.log
mongod --shardsvr --dbpath /disk1/data/db/shard0/rs1 --port 27001 --fork --replSet shard0 --logpath /disk1/logs/shard0-rs1.log

sleep 10

echo "connecting to a server to initialize the set"
mongo --port 27000 << 'EOF'
config = {
    _id: 'shard0', members: [
        {_id: 0, host: 'localhost:27000'},
        {_id: 1, host: 'localhost:27001'},
    ]
}
rs.initiate(config)
EOF

echo "start a replica set on a shard1"
mkdir -p /disk1/data/db/shard1/rs0 /disk1/data/db/shard1/rs1
mongod --shardsvr --dbpath /disk1/data/db/shard1/rs0 --port 37000 --fork --replSet shard1 --logpath /disk1/logs/shard1-rs0.log
mongod --shardsvr --dbpath /disk1/data/db/shard1/rs1 --port 37001 --fork --replSet shard1 --logpath /disk1/logs/shard1-rs1.log

sleep 10

echo "connecting to a server to initialize the set"
mongo --port 37000 << 'EOF'
config = {
    _id: 'shard1', members: [
        {_id: 0, host: 'localhost:37000'},
        {_id: 1, host: 'localhost:37001'},
    ]
}
rs.initiate(config)
EOF

echo "setup config servers"
mkdir -p /disk1/data/db/config
mongod --configsvr --dbpath /disk1/data/db/config --port 47000 --fork --logpath /disk1/logs/config.log

echo "starting mongos"
mongos --configdb 50.97.182.67:47000,50.97.182.68:47000,50.97.182.69:47000 --fork --logpath /disk1/logs/mongos.log

echo "waiting for a replica set to come online"
sleep 60
echo "connnecting to mongos and enabling sharding"

