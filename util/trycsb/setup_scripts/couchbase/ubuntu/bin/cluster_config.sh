#!/bin/bash

if [ -z "$1" ]; then
    echo "Host address required"
    exit 1
fi

export PATH=$PATH:/opt/couchbase/bin

COUCHBASE_CURRENT_NODE=$1
COUCHBASE_PORT="8091"
COUCHBASE_USER="couchbase"
COUCHBASE_PASSWORD="couchbase"

COUCHBASE_MAIN_NODE="192.155.206.162"
COUCHBASE_NODE_1="192.155.206.163"
COUCHBASE_NODE_2="50.23.195.162"

COUCHBASE_CLUSTER_RAMSIZE="81920"
COUCHBASE_BUCKET_NAME="default"
COUCHBASE_BUCKET_TYPE="couchbase"
COUCHBASE_BUCKET_RAMSIZE="81920"
COUCHBASE_BUCKET_REPLICA="0"
COUCHBASE_ENABLE_FLUSH="1"

COUCHBASE_DATA_PATH=/disk1/couchbase/data
COUCHBASE_INDEX_PATH=/opt/couchbase/var/lib/couchbase/index

mkdir -p ${COUCHBASE_DATA_PATH} ${COUCHBASE_INDEX_PATH}
chown couchbase:couchbase ${COUCHBASE_DATA_PATH} ${COUCHBASE_INDEX_PATH}
chmod -R u=rwx ${COUCHBASE_DATA_PATH} ${COUCHBASE_INDEX_PATH}

echo " * node initialization at $COUCHBASE_CURRENT_NODE"
couchbase-cli node-init -c ${COUCHBASE_CURRENT_NODE}:${COUCHBASE_PORT} \
                        --node-init-data-path=${COUCHBASE_DATA_PATH} \
                        --node-init-index-path=${COUCHBASE_INDEX_PATH} \
                        -u ${COUCHBASE_USER} \
                        -p ${COUCHBASE_PASSWORD}

sleep 4

if [ "$1" == "$COUCHBASE_MAIN_NODE" ]; then

    echo " * cluster initialization at $COUCHBASE_MAIN_NODE"
    couchbase-cli cluster-init -c ${COUCHBASE_MAIN_NODE}:${COUCHBASE_PORT} \
                               --cluster-username=${COUCHBASE_USER} \
                               --cluster-password=${COUCHBASE_PASSWORD} \
                               --cluster-ramsize=${COUCHBASE_CLUSTER_RAMSIZE} \
                               -u ${COUCHBASE_USER} \
                               -p ${COUCHBASE_PASSWORD}

    sleep 1

    echo " * create bucket at $COUCHBASE_MAIN_NODE"
    couchbase-cli bucket-create -c ${COUCHBASE_MAIN_NODE}:${COUCHBASE_PORT} \
                                --bucket=${COUCHBASE_BUCKET_NAME} \
                                --bucket-type=${COUCHBASE_BUCKET_TYPE} \
                                --bucket-ramsize=${COUCHBASE_BUCKET_RAMSIZE} \
                                --bucket-replica=${COUCHBASE_BUCKET_REPLICA} \
                                --enable-flush=${COUCHBASE_ENABLE_FLUSH} \
                                --wait \
                                -u ${COUCHBASE_USER} \
                                -p ${COUCHBASE_PASSWORD}

    sleep 10

    echo " * add nodes to cluster"
    couchbase-cli rebalance -c ${COUCHBASE_MAIN_NODE}:${COUCHBASE_PORT} \
                            --server-add=${COUCHBASE_NODE_1}:${COUCHBASE_PORT} \
                            --server-add=${COUCHBASE_NODE_2}:${COUCHBASE_PORT} \
                            --server-add-username=${COUCHBASE_USER} \
                            --server-add-password=${COUCHBASE_PASSWORD} \
                            -u ${COUCHBASE_USER} \
                            -p ${COUCHBASE_PASSWORD}

    else
    exit 0
fi