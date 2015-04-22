#!/bin/bash

if [ -z "$1" ]; then
    echo "Host address required"
    exit 1
fi

export PATH=$PATH:/opt/couchbase/bin

COUCHBASE_MAIN_NODE="192.155.206.162"
COUCHBASE_PORT="8091"
COUCHBASE_USER="couchbase"
COUCHBASE_PASSWORD="couchbase"
COUCHBASE_CLUSTER_RAMSIZE="81920"
COUCHBASE_BUCKET_NAME="default"
COUCHBASE_BUCKET_TYPE="couchbase"
COUCHBASE_BUCKET_RAMSIZE="81920"
COUCHBASE_BUCKET_REPLICA="1"

if [ "$1" == "192.155.206.162" ]; then

    echo "cluster initialization at $COUCHBASE_MAIN_NODE"
    couchbase-cli cluster-init -c ${COUCHBASE_MAIN_NODE}:${COUCHBASE_PORT} --cluster-username=${COUCHBASE_USER} --cluster-password=${COUCHBASE_PASSWORD} --cluster-ramsize=${COUCHBASE_CLUSTER_RAMSIZE} -u ${COUCHBASE_USER} -p ${COUCHBASE_PASSWORD}

    echo "create bucket at $COUCHBASE_MAIN_NODE"
    couchbase-cli bucket-create -c ${COUCHBASE_MAIN_NODE}:${COUCHBASE_PORT} --bucket=${COUCHBASE_BUCKET_NAME} --bucket-type=${COUCHBASE_BUCKET_TYPE} --bucket-ramsize=${COUCHBASE_BUCKET_RAMSIZE} --bucket-replica=${COUCHBASE_BUCKET_REPLICA} --enable-flush=0 --wait -u ${COUCHBASE_USER} -p ${COUCHBASE_PASSWORD}

    else
    exit 0
fi