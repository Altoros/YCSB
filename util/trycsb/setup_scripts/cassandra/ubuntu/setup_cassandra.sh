#!/bin/bash

if [ -z "$1" ]; then
    echo "Host address required"
    exit 1
fi

DSC_VERSION=22
CASSANDRA_VERSION=2.2.3

bash bin/uninstall_dse.sh $DSC_VERSION
bash bin/install_dse.sh $DSC_VERSION $CASSANDRA_VERSION
bash bin/cluster_config.sh $1 