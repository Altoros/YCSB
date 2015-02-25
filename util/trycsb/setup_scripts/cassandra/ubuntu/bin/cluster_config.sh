#!/bin/bash

script_name=`basename $0`

if [ -z "$1" ]; then
    echo "Host address required"
    exit 1
fi


CHANGE_MARK="# changed"
CURRENT_HOST_ADDR=$1
CASSANDRA_CONF_DIR=/etc/cassandra
CASSANDRA_CONF=${CASSANDRA_CONF_DIR}/cassandra.yaml
CASSANDRA_ENV_CONF=${CASSANDRA_CONF_DIR}/cassandra-env.sh
CASSANDRA_DATA_DIR=/var/cassandra-data
CASSANDRA_COMMITLOG_DIR=/disk1/cassandra-commitlog
SEEDS="192.155.206.162"

declare -A LOCAL_ADDRESSES
#LOCAL_ADDRESSES['192.155.206.162']="10.84.163.167"
#LOCAL_ADDRESSES['192.155.206.163']="10.84.163.169"
#LOCAL_ADDRESSES['50.23.195.162']="10.80.194.56"
LOCAL_ADDRESSES['192.155.206.162']="192.155.206.162"
LOCAL_ADDRESSES['192.155.206.163']="192.155.206.163"
LOCAL_ADDRESSES['50.23.195.162']="50.23.195.162"

declare -A TOKENS
TOKENS['192.155.206.162']="-9223372036854775808"
TOKENS['192.155.206.163']="-3074457345618258603"
TOKENS['50.23.195.162']="3074457345618258602"


rm -fR /var/log/cassandra/*


echo "$script_name: Create/clear $CASSANDRA_COMMITLOG_DIR"
if [ -z "$CASSANDRA_COMMITLOG_DIR" ]; then
    echo "Cassandra commitlog dir unspecified"
    exit 1
fi

mkdir -p ${CASSANDRA_COMMITLOG_DIR}
rm -fR ${CASSANDRA_COMMITLOG_DIR}/*
chown cassandra:cassandra ${CASSANDRA_COMMITLOG_DIR}

echo "$script_name: Create/clear $CASSANDRA_DATA_DIR"
if [ -z "$CASSANDRA_DATA_DIR" ]; then
    echo "Cassandra data dir unspecified"
    exit 1
fi

mkdir -p ${CASSANDRA_DATA_DIR}
rm -fR ${CASSANDRA_DATA_DIR}/*
chown cassandra:cassandra ${CASSANDRA_DATA_DIR}


echo "$script_name: Replace cassandra configs"
cp conf/cassandra-topology.properties ${CASSANDRA_CONF_DIR}/cassandra-topology.properties

echo "$script_name: Change ${CASSANDRA_CONF} settings"
sed -i "s|num_tokens: 256|num_tokens: ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|# initial_token:|initial_token: ${TOKENS[$CURRENT_HOST_ADDR]} ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|- seeds: \"127.0.0.1\"|- seeds: \"${SEEDS}\" ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|- /var/lib/cassandra/data|- ${CASSANDRA_DATA_DIR} ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|commitlog_directory: /var/lib/cassandra/commitlog|commitlog_directory: ${CASSANDRA_COMMITLOG_DIR} ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|listen_address: localhost|listen_address: ${LOCAL_ADDRESSES[$CURRENT_HOST_ADDR]} ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|rpc_address: localhost|rpc_address: $CURRENT_HOST_ADDR ${CHANGE_MARK}|g" ${CASSANDRA_CONF}

#sed -i "s|row_cache_size_in_mb: 0|row_cache_size_in_mb: 0 ${CHANGE_MARK}|g" $CASSANDRA_CONF
#sed -i "s|concurrent_reads: 32|concurrent_reads: 16 ${CHANGE_MARK}|g" $CASSANDRA_CONF
sed -i "s|concurrent_writes: 32|concurrent_writes: 1024 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|memtable_allocation_type: heap_buffers|memtable_allocation_type: offheap_objects ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|# memtable_offheap_space_in_mb: 2048|memtable_offheap_space_in_mb: 71680 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|#memtable_flush_writers: 8|memtable_flush_writers: 3 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|# native_transport_max_threads: 128|native_transport_max_threads: 1024 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|#concurrent_compactors: 1|concurrent_compactors: 2 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|compaction_throughput_mb_per_sec: 16|compaction_throughput_mb_per_sec: 256 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|# memtable_cleanup_threshold: 0.11|memtable_cleanup_threshold: 0.35 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|write_request_timeout_in_ms: 2000|write_request_timeout_in_ms: 180000 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|read_request_timeout_in_ms: 5000|read_request_timeout_in_ms: 180000 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}

echo "$script_name: Change ${CASSANDRA_ENV_CONF} settings"
sed -i "s|#MAX_HEAP_SIZE=\"4G\"|MAX_HEAP_SIZE=\"8G\" ${CHANGE_MARK}|g" ${CASSANDRA_ENV_CONF}
sed -i "s|#HEAP_NEWSIZE=\"800M\"|HEAP_NEWSIZE=\"1600M\" ${CHANGE_MARK}|g" ${CASSANDRA_ENV_CONF}
sed -i "s|JVM_OPTS=\"\$JVM_OPTS -ea\"|JVM_OPTS=\"\$JVM_OPTS -da\" ${CHANGE_MARK}|g" ${CASSANDRA_ENV_CONF}