#!/bin/bash

if [ -z "$1" ]; then
    echo "Host address required"
    exit 1
fi

bash bin/uninstall_couchbase.sh
bash bin/install_couchbase.sh
sleep 10
bash bin/node_init.sh $1 #on all nodes
sleep 2
bash bin/cluster_init.sh $1 #only on main node
sleep 2
bash bin/cluster_config.sh $1 #only on node1 & node2