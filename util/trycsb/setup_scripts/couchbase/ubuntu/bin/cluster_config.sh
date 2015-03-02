#!/bin/bash

if [ -z "$1" ]; then
    echo "Host address required"
    exit 1
fi

export PATH=$PATH:/opt/couchbase/bin

COUCHBASE_MAIN_NODE="192.155.206.162"
COUCHBASE_CURRENT_NODE=$1
COUCHBASE_NODE2="50.23.195.162"
COUCHBASE_PORT="8091"
COUCHBASE_USER="couchbase"
COUCHBASE_PASSWORD="couchbase"

echo "add node $COUCHBASE_CURRENT_NODE to cluster"
couchbase-cli server-add -c ${COUCHBASE_MAIN_NODE}:${COUCHBASE_PORT} --server-add=${COUCHBASE_CURRENT_NODE}:${COUCHBASE_PORT} -u ${COUCHBASE_USER} -p ${COUCHBASE_PASSWORD}