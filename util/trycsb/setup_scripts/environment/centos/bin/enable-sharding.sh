#!/bin/sh

MONGODB_DIST_DIR=/home/altoros/mongodb-linux-x86_64-2.6.7

$MONGODB_DIST_DIR/bin/mongos --configdb 192.155.206.162:57000,192.155.206.163:57000,50.23.195.162:57000\
--fork --logpath /disk1/mongodb-logs/mongos.log --noAutoSplit &


$MONGODB_DIST_DIR/bin/mongo << 'EOF'
    sh.addShard("shard0/192.155.206.162:27000,50.23.195.162:27000")
    sh.addShard("shard1/192.155.206.162:37000,192.155.206.163:37000")
    sh.addShard("shard2/50.23.195.162:37000,192.155.206.163:27000")
    sh.enableSharding("ycsb")
    sh.shardCollection("ycsb.usertable", {"_id":"hashed"})
    sh.stopBalancer()
EOF

