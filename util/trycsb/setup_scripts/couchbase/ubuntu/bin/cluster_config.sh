#!/bin/bash

export PATH=$PATH:/opt/couchbase/bin

COUCHBASE_CURRENT_NODE="192.155.206.162"
COUCHBASE_NODE1="192.155.206.163"
COUCHBASE_NODE2="50.23.195.162"
COUCHBASE_PORT="8091"
COUCHBASE_USER="couchbase"
COUCHBASE_PASSWORD="couchbase"

COUCHBASE_DATA_PATH=/opt/couchbase/var/lib/couchbase/data
COUCHBASE_INDEX_PATH=/disk1/couchbase/index

#TODO create path with $mkdir and $chown to couchbase

COUCHBASE_CLUSTER_RAMSIZE="1000"

COUCHBASE_BUCKET_NAME="default"
COUCHBASE_BUCKET_TYPE="couchbase"
COUCHBASE_BUCKET_RAMSIZE="700"

echo "node initialization"
couchbase-cli node-init -c ${COUCHBASE_CURRENT_NODE}:${COUCHBASE_PORT} --node-init-data-path=${COUCHBASE_DATA_PATH} --node-init-index-path=${COUCHBASE_INDEX_PATH} -u ${COUCHBASE_USER} -p ${COUCHBASE_PASSWORD}

echo "cluster initialization"
couchbase-cli cluster-init -c ${COUCHBASE_CURRENT_NODE}:${COUCHBASE_PORT} --cluster-username=${COUCHBASE_USER} --cluster-password=${COUCHBASE_PASSWORD} --cluster-ramsize=${COUCHBASE_CLUSTER_RAMSIZE} -u ${COUCHBASE_USER} -p ${COUCHBASE_PASSWORD}

echo "create bucket"
couchbase-cli bucket-create -c ${COUCHBASE_CURRENT_NODE}:${COUCHBASE_PORT} --bucket=${COUCHBASE_BUCKET_NAME} --bucket-type=${COUCHBASE_BUCKET_TYPE} --bucket-ramsize=${COUCHBASE_BUCKET_RAMSIZE} -u ${COUCHBASE_USER} -p ${COUCHBASE_PASSWORD}

echo "add nodes to cluster"
couchbase-cli server-add -c ${COUCHBASE_CURRENT_NODE}:${COUCHBASE_PORT} --server-add=${COUCHBASE_NODE1}:${COUCHBASE_PORT} -u ${COUCHBASE_USER} -p ${COUCHBASE_PASSWORD}
couchbase-cli server-add -c ${COUCHBASE_CURRENT_NODE}:${COUCHBASE_PORT} --server-add=${COUCHBASE_NODE2}:${COUCHBASE_PORT} -u ${COUCHBASE_USER} -p ${COUCHBASE_PASSWORD}