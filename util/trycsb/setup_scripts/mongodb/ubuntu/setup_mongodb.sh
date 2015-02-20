#!/bin/sh

if [ -z "$1" ]; then
    echo "Host address required"
    exit 1
fi

bash bin/install_mongo.sh
#bash bin/setup_cluster.sh $1
#bash bin/uninstall_mongo.sh
