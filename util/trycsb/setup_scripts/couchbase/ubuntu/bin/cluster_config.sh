#!/bin/bash

export PATH=$PATH:/opt/couchbase/bin

CURRENT_NODE="192.155.206.162"
NODE1="192.155.206.163"
NODE2="50.23.195.162"
PORT="8091"
USER="couchbase"
PASS="couchbase"

COUCHBASE_DATA_PATH=/disk1/data
COUCHBASE_INDEX_PATH=/tmp/index

COUCHBASE_CLUSTER_USERNAME=${USER}
COUCHBASE_CLUSTER_PASSWORD=${PASS}
COUCHBASE_CLUSTER_RAMSIZE="10000"

COUCHBASE_BUCKET_NAME="default"
COUCHBASE_BUCKET_TYPE="couchbase"
COUCHBASE_BUCKET_RAMSIZE="7000"

echo "node initialization"
couchbase-cli node-init -c ${CURRENT_NODE}:${PORT} --node-init-data-path=${COUCHBASE_DATA_PATH} --node-init-index-path=${COUCHBASE_INDEX_PATH} -u ${USER} -p ${PASS}

echo "cluster initialization"
couchbase-cli cluster-init -c ${CURRENT_NODE}:${PORT} --cluster-username=${COUCHBASE_CLUSTER_USERNAME} --cluster-password=${COUCHBASE_CLUSTER_PASSWORD} --cluster-ramsize=${COUCHBASE_CLUSTER_RAMSIZE} -u ${USER} -p ${PASS}

echo "create bucket"
couchbase-cli bucket-create -c ${CURRENT_NODE}:${PORT} --bucket=${COUCHBASE_BUCKET_NAME} --bucket-type=${COUCHBASE_BUCKET_TYPE} --bucket-ramsize=${COUCHBASE_BUCKET_RAMSIZE} -u ${USER} -p ${PASS}

echo "add nodes to cluster"
couchbase-cli server-add -c ${CURRENT_NODE}:${PORT} --server-add=${NODE1}:${PORT} -u ${USER} -p ${PASS}
couchbase-cli server-add -c ${CURRENT_NODE}:${PORT} --server-add=${NODE2}:${PORT} -u ${USER} -p ${PASS}