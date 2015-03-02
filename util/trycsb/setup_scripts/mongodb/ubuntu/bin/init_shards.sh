#!/bin/sh

if [ -z "$1" ]; then
    echo "Host address required"
    exit 1
fi

CURRENT_HOST_ADDRESS=$1

if [ $CURRENT_HOST_ADDRESS = "50.23.195.162" ]; then
    mongo --host $CURRENT_HOST_ADDRESS --port 27000 << 'EOF'
    config = { _id : "shard0",
                members : [{ _id : 0, host : "50.23.195.162:27000"},
                           { _id : 1, host : "192.155.206.162:27000"} ]
             };
    rs.initiate(config)
EOF
fi

if [ $CURRENT_HOST_ADDRESS = "192.155.206.162" ]; then
    mongo --host $CURRENT_HOST_ADDRESS --port 37000 << 'EOF'
    config = { _id : "shard1",
                members : [{ _id : 0, host : "192.155.206.162:37000"},
                           { _id : 1, host : "192.155.206.163:37000"}]
             };
    rs.initiate(config)
EOF
fi

if [ $CURRENT_HOST_ADDRESS = "192.155.206.163" ]; then
    mongo --host $CURRENT_HOST_ADDRESS --port 27000 << 'EOF'
    config = { _id : "shard2",
            members : [{ _id : 0, host : "192.155.206.163:27000"},
                       { _id : 1, host : "50.23.195.162:37000"}]
         };
    rs.initiate(config)
EOF
fi