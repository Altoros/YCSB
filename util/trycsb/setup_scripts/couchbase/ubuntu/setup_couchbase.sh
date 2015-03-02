#!/bin/bash

if [ -z "$1" ]; then
    echo "Host address required"
    exit 1
fi

bash bin/uninstall_couchbase.sh
bash bin/install_couchbase.sh
bash bin/node_init.sh $1 #runs on all nodes
sleep 10
bash bin/cluster_init.sh $1 #runs only on main node
sleep 10
bash bin/cluster_config.sh $1 #runs only on node1 & node2