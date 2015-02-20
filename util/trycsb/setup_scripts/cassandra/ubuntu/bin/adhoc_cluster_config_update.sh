#!/bin/bash

if [ -z "$1" ]; then
    echo "Host address required"
    exit 1
fi


CHANGE_MARK="# changed"
CURRENT_HOST_ADDR=$1
CASSANDRA_CONF_DIR=/etc/cassandra
CASSANDRA_CONF=$CASSANDRA_CONF_DIR/cassandra.yaml
CASSANDRA_ENV_CONF=$CASSANDRA_CONF_DIR/cassandra-env.sh
CASSANDRA_DATA_DIR=/var/cassandra-data
CASSANDRA_COMMITLOG_DIR=/disk1/cassandra-commitlog

echo "Change config settings"
sed -i "s|row_cache_size_in_mb: 0|row_cache_size_in_mb: 30720 $CHANGE_MARK|g" $CASSANDRA_CONF
sed -i "s|concurrent_reads: 32|concurrent_reads: 16 $CHANGE_MARK|g" $CASSANDRA_CONF
sed -i "s|concurrent_writes: 32|concurrent_writes: 128 $CHANGE_MARK|g" $CASSANDRA_CONF
sed -i "s|memtable_allocation_type: heap_buffers|memtable_allocation_type: offheap_buffers $CHANGE_MARK|g" $CASSANDRA_CONF
sed -i "s|# memtable_offheap_space_in_mb: 2048|memtable_offheap_space_in_mb: 8192 $CHANGE_MARK|g" $CASSANDRA_CONF
sed -i "s|#memtable_flush_writers: 8|memtable_flush_writers: 5 $CHANGE_MARK|g" $CASSANDRA_CONF
sed -i "s|# native_transport_max_threads: 128|native_transport_max_threads: 128 $CHANGE_MARK|g" $CASSANDRA_CONF
sed -i "s|#concurrent_compactors: 1|concurrent_compactors: 2 $CHANGE_MARK|g" $CASSANDRA_CONF
sed -i "s|compaction_throughput_mb_per_sec: 16|compaction_throughput_mb_per_sec: 64 $CHANGE_MARK|g" $CASSANDRA_CONF

sed -i "s|#MAX_HEAP_SIZE=\"4G\"|MAX_HEAP_SIZE=\"8G\" $CHANGE_MARK|g" $CASSANDRA_ENV_CONF
sed -i "s|#HEAP_NEWSIZE=\"800M\"|HEAP_NEWSIZE=\"1600M\" $CHANGE_MARK|g" $CASSANDRA_ENV_CONF
sed -i "s|JVM_OPTS=\"$JVM_OPTS -ea\"|JVM_OPTS=\"$JVM_OPTS -da\" $CHANGE_MARK|g" $CASSANDRA_ENV_CONF
