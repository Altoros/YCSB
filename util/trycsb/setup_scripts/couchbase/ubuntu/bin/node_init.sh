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

COUCHBASE_DATA_PATH=/opt/couchbase/var/lib/couchbase/data
COUCHBASE_INDEX_PATH=/disk1/couchbase/index

mkdir -p ${COUCHBASE_DATA_PATH} ${COUCHBASE_INDEX_PATH}
chown couchbase:couchbase ${COUCHBASE_DATA_PATH} ${COUCHBASE_INDEX_PATH}
chmod -R u=rwx ${COUCHBASE_DATA_PATH} ${COUCHBASE_INDEX_PATH}

echo "node initialization at $COUCHBASE_CURRENT_NODE"
couchbase-cli node-init -c ${COUCHBASE_CURRENT_NODE}:${COUCHBASE_PORT} --node-init-data-path=${COUCHBASE_DATA_PATH} --node-init-index-path=${COUCHBASE_INDEX_PATH} -u ${COUCHBASE_USER} -p ${COUCHBASE_PASSWORD}