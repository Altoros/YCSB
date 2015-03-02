#!/bin/sh

mongo << 'EOF'
    db.adminCommand({ addshard : "shard0/192.155.206.162:27000,50.23.195.162:27000"})
    db.adminCommand({ addshard : "shard1/192.155.206.162:37000,192.155.206.163:37000"})
    db.adminCommand({ addshard : "shard2/50.23.195.162:37000,192.155.206.163:27000"})
    db.adminCommand({enablesharding : "ycsb"})
    db.adminCommand({shardCollection : "ycsb.usertable", key : {_id:"hashed"}})
    sh.stopBalancer()
EOF

sleep 10
mongos --configdb 192.155.206.162:57000,192.155.206.163:57000,50.23.195.162:57000 --fork --logpath /disk1/mongodb-logs/mongos.log
