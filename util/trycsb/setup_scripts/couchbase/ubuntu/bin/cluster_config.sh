#!/bin/bash

if [ -z "$1" ]; then
    echo "Host address required"
    exit 1
fi

export PATH=$PATH:/opt/couchbase/bin

COUCHBASE_MAIN_NODE=$1
COUCHBASE_NODE_1="192.155.206.163"
COUCHBASE_NODE_2="50.23.195.162"
COUCHBASE_PORT="8091"
COUCHBASE_USER="couchbase"
COUCHBASE_PASSWORD="couchbase"

if [ "$1" == "192.155.206.162" ]; then

    echo "add nodes to cluster"
    couchbase-cli rebalance -c ${COUCHBASE_MAIN_NODE}:${COUCHBASE_PORT} --server-add=${COUCHBASE_NODE_1}:${COUCHBASE_PORT} --server-add=${COUCHBASE_NODE_2}:${COUCHBASE_PORT} --server-add-username=${COUCHBASE_USER} --server-add-password=${COUCHBASE_PASSWORD} -u ${COUCHBASE_USER} -p ${COUCHBASE_PASSWORD}

    else
    exit 0
fi