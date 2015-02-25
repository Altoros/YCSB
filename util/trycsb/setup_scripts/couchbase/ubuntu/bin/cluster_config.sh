#!/bin/bash

if [ -z "$1" ]; then
    echo "Username required"
    exit 1
fi

if [ -z "$2" ]; then
    echo "Password required"
    exit 1
fi

CURRENT_NODE="192.155.206.162"
NODE1="192.155.206.163"
NODE2="50.23.195.162"
PORT="8091"
USER=$1
PASS=$2

COUCHBASE_DATA_PATH=/tmp/data
COUCHBASE_INDEX_PATH=/tmp/index

COUCHBASE_CLUSTER_USERNAME=${USER}
COUCHBASE_CLUSTER_PASSWORD=${PASS}
COUCHBASE_CLUSTER_RAMSIZE="1000"

COUCHBASE_BUCKET_NAME="default"
COUCHBASE_BUCKET_TYPE="couchbase"
COUCHBASE_BUCKET_RAMSIZE="1000"

echo "node initialization"
couchbase-cli node-init -c ${CURRENT_NODE}:${PORT} --node-init-data-path=${COUCHBASE_DATA_PATH} --node-init-index-path=${COUCHBASE_INDEX_PATH} -u ${USER} -p ${PASS}

echo "cluster initialization"
couchbase-cli cluster-init -c ${CURRENT_NODE}:${PORT} --cluster-username=${COUCHBASE_CLUSTER_USERNAME} --cluster-password=${COUCHBASE_CLUSTER_PASSWORD} --cluster-ramsize=${COUCHBASE_CLUSTER_RAMSIZE}

echo "create bucket"
couchbase-cli bucket-create -c ${CURRENT_NODE}:${PORT} --bucket=${COUCHBASE_BUCKET_NAME} --bucket-type=${COUCHBASE_BUCKET_TYPE} --bucket-ramsize=${COUCHBASE_BUCKET_RAMSIZE} -u ${USER} -p ${PASS}

echo "add nodes to cluster"
couchbase-cli server-add -c ${CURRENT_NODE}:${PORT} --server-add=${NODE1}:${PORT} -u ${USER} -p ${PASS}
couchbase-cli server-add -c ${CURRENT_NODE}:${PORT} --server-add=${NODE2}:${PORT} -u ${USER} -p ${PASS}

echo "list servers in cluster"
couchbase-cli server-list -c ${CURRENT_NODE}:${PORT}

echo "erver information"
couchbase-cli server-info -c ${CURRENT_NODE}:${PORT} -u ${USER} -p ${PASS}
