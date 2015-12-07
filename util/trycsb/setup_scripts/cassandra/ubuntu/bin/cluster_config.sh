#!/bin/bash

script_name=`basename $0`

if [ -z "$1" ]; then
    echo "Public host address required"
    exit 1
fi


sleep 30
echo "$script_name: Stopping Cassandra"
service cassandra stop
service datastax-agent stop
service opscenterd stop


CHANGE_MARK="# changed"
CURRENT_HOST_ADDR=$1
CASSANDRA_CONF_DIR=/etc/cassandra
CASSANDRA_CONF=${CASSANDRA_CONF_DIR}/cassandra.yaml
CASSANDRA_ENV_CONF=${CASSANDRA_CONF_DIR}/cassandra-env.sh
CASSANDRA_DATA_DIR=/var/cassandra-data
CASSANDRA_COMMITLOG_DIR=/disk1/cassandra-commitlog
#!/bin/bash

SEEDS="192.168.2.48,192.168.2.50,192.168.2.52"
seedsArr=(${SEEDS//,/ })
seedsArrLen=${#seedsArr[@]}

all_token_range=$(echo '2^64' | bc)
start_token_range=$(echo '-2^63' | bc)
token_step=$(bc <<< "$all_token_range/$seedsArrLen")

declare -A PUBLIC_TO_LOCAL_ADDRESSES
for i in "${!seedsArr[@]}"
do
    seed=${seedsArr[i]}
    PUBLIC_TO_LOCAL_ADDRESSES[$seed]=$seed
done

declare -A PUBLIC_ADDRESS_TO_TOKEN
for i in "${!seedsArr[@]}"
do
    seed=${seedsArr[i]}
    PUBLIC_ADDRESS_TO_TOKEN[$seed]=$(bc <<< $start_token_range+$token_step*$i)
done


rm -fr /var/log/cassandra/*
rm -r /var/lib/cassandra/commitlog/*
rm -r /var/lib/cassandra/data/*
rm -r /var/lib/cassandra/saved_caches/*


echo "$script_name: Create/clear $CASSANDRA_COMMITLOG_DIR"
if [ -z "$CASSANDRA_COMMITLOG_DIR" ]; then
    echo "Cassandra commitlog dir unspecified"
    exit 1
fi

mkdir -p ${CASSANDRA_COMMITLOG_DIR}
rm -fr ${CASSANDRA_COMMITLOG_DIR}/*
chown cassandra:cassandra ${CASSANDRA_COMMITLOG_DIR}

echo "$script_name: Create/clear $CASSANDRA_DATA_DIR"
if [ -z "$CASSANDRA_DATA_DIR" ]; then
    echo "Cassandra data dir unspecified"
    exit 1
fi

mkdir -p ${CASSANDRA_DATA_DIR}
rm -fr ${CASSANDRA_DATA_DIR}/*
chown cassandra:cassandra ${CASSANDRA_DATA_DIR}


echo "$script_name: Replace cassandra configs"
cp conf/cassandra-topology.properties ${CASSANDRA_CONF_DIR}/cassandra-topology.properties

echo "$script_name: Change ${CASSANDRA_CONF} settings"
sed -i "s|num_tokens: 256|num_tokens: ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|# initial_token:|initial_token: ${PUBLIC_ADDRESS_TO_TOKEN[$CURRENT_HOST_ADDR]} ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|- seeds: \"127.0.0.1\"|- seeds: \"${SEEDS}\" ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|- /var/lib/cassandra/data|- ${CASSANDRA_DATA_DIR} ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|commitlog_directory: /var/lib/cassandra/commitlog|commitlog_directory: ${CASSANDRA_COMMITLOG_DIR} ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|listen_address: localhost|listen_address: ${PUBLIC_TO_LOCAL_ADDRESSES[$CURRENT_HOST_ADDR]} ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|rpc_address: localhost|rpc_address: $CURRENT_HOST_ADDR ${CHANGE_MARK}|g" ${CASSANDRA_CONF}

#sed -i "s|key_cache_size_in_mb:|key_cache_size_in_mb: 128 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
#sed -i "s|row_cache_size_in_mb: 0|row_cache_size_in_mb: 10240 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|memtable_allocation_type: heap_buffers|memtable_allocation_type: offheap_objects ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|# memtable_heap_space_in_mb: 2048|memtable_heap_space_in_mb: 20480 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|# memtable_offheap_space_in_mb: 2048|memtable_offheap_space_in_mb: 20480 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|# memtable_cleanup_threshold: 0.11|memtable_cleanup_threshold: 0.02 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|#memtable_flush_writers: 8|memtable_flush_writers: 24 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|# commitlog_total_space_in_mb: 8192|commitlog_total_space_in_mb: 10124 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|commitlog_sync_period_in_ms: 10000|commitlog_sync_period_in_ms: 5000 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
#sed -i "s|commitlog_sync: periodic|#commitlog_sync: periodic ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
#sed -i "s|# commitlog_sync: batch|commitlog_sync: batch ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
#sed -i "s|# commitlog_sync_batch_window_in_ms: 50|commitlog_sync_batch_window_in_ms: 30 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|concurrent_reads: 32|concurrent_reads: 24 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|concurrent_writes: 32|concurrent_writes: 196 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|# native_transport_max_threads: 128|native_transport_max_threads: 99000000 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
#sed -i "s|#concurrent_compactors: 1|concurrent_compactors: 1 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
#sed -i "s|compaction_throughput_mb_per_sec: 16|compaction_throughput_mb_per_sec: 64 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|write_request_timeout_in_ms: 2000|write_request_timeout_in_ms: 180000 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
sed -i "s|read_request_timeout_in_ms: 5000|read_request_timeout_in_ms: 180000 ${CHANGE_MARK}|g" ${CASSANDRA_CONF}
#sed -i "s|trickle_fsync: false|trickle_fsync: true ${CHANGE_MARK}|g" ${CASSANDRA_CONF}

echo "$script_name: Change ${CASSANDRA_ENV_CONF} settings"
echo -e '# OptionPlaceholder a0' >> ${CASSANDRA_ENV_CONF}
echo -e '# OptionPlaceholder a1' >> ${CASSANDRA_ENV_CONF}
echo -e '# OptionPlaceholder a2' >> ${CASSANDRA_ENV_CONF}
echo -e '# OptionPlaceholder a3' >> ${CASSANDRA_ENV_CONF}
echo -e '# OptionPlaceholder a4' >> ${CASSANDRA_ENV_CONF}
echo -e '# OptionPlaceholder a5' >> ${CASSANDRA_ENV_CONF}
echo -e '# OptionPlaceholder a6' >> ${CASSANDRA_ENV_CONF}
echo -e '# OptionPlaceholder a7' >> ${CASSANDRA_ENV_CONF}
echo -e '# OptionPlaceholder a8' >> ${CASSANDRA_ENV_CONF}
echo -e '# OptionPlaceholder a9' >> ${CASSANDRA_ENV_CONF}
echo -e '# OptionPlaceholder b1' >> ${CASSANDRA_ENV_CONF}

sed -i "s|JVM_OPTS=\"\$JVM_OPTS -ea\"|JVM_OPTS=\"\$JVM_OPTS -da\" ${CHANGE_MARK}|g" ${CASSANDRA_ENV_CONF}

# https://issues.apache.org/jira/browse/CASSANDRA-8150
sed -i "s|#MAX_HEAP_SIZE=\"4G\"|MAX_HEAP_SIZE=\"45G\" ${CHANGE_MARK}|g" ${CASSANDRA_ENV_CONF}
sed -i "s|#HEAP_NEWSIZE=\"800M\"|HEAP_NEWSIZE=\"40G\" ${CHANGE_MARK}|g" ${CASSANDRA_ENV_CONF}

sed -i "s|JVM_OPTS=\"\$JVM_OPTS -XX:MaxTenuringThreshold=1\"|JVM_OPTS=\"\$JVM_OPTS -XX:MaxTenuringThreshold=8\"|g" ${CASSANDRA_ENV_CONF}

sed -i "s|# OptionPlaceholder a0|JVM_OPTS=\"\$JVM_OPTS -XX:ParallelGCThreads=20\"|g" ${CASSANDRA_ENV_CONF}
sed -i "s|# OptionPlaceholder a1|JVM_OPTS=\"\$JVM_OPTS -XX:ConcGCThreads=20\"|g" ${CASSANDRA_ENV_CONF}

sed -i "s|# OptionPlaceholder a2|JVM_OPTS=\"\$JVM_OPTS -XX:+CMSScavengeBeforeRemark\"|g" ${CASSANDRA_ENV_CONF}
sed -i "s|# OptionPlaceholder a3|JVM_OPTS=\"\$JVM_OPTS -XX:CMSMaxAbortablePrecleanTime=60000\"|g" ${CASSANDRA_ENV_CONF}
sed -i "s|# OptionPlaceholder a4|JVM_OPTS=\"\$JVM_OPTS -XX:CMSWaitDuration=100000\"|g" ${CASSANDRA_ENV_CONF}

sed -i "s|# OptionPlaceholder a5|JVM_OPTS=\"\$JVM_OPTS -XX:+UnlockDiagnosticVMOptions\"|g" ${CASSANDRA_ENV_CONF}
sed -i "s|# OptionPlaceholder a6|JVM_OPTS=\"\$JVM_OPTS -XX:+UseGCTaskAffinity\"|g" ${CASSANDRA_ENV_CONF}
sed -i "s|# OptionPlaceholder a7|JVM_OPTS=\"\$JVM_OPTS -XX:+BindGCTaskThreadsToCPUs\"|g" ${CASSANDRA_ENV_CONF}
sed -i "s|# OptionPlaceholder a8|JVM_OPTS=\"\$JVM_OPTS -XX:ParGCCardsPerStrideChunk=32768\"|g" ${CASSANDRA_ENV_CONF}
sed -i "s|# OptionPlaceholder a9|JVM_OPTS=\"\$JVM_OPTS -XX:MaxGCPauseMillis=20\"|g" ${CASSANDRA_ENV_CONF}
sed -i "s|# OptionPlaceholder b1|JVM_OPTS=\"\$JVM_OPTS -XX:+CMSConcurrentMTEnabled\"|g" ${CASSANDRA_ENV_CONF}

#https://issues.apache.org/jira/browse/CASSANDRA-9822
sed -i "s|CMD_PATT=\"cassandra.+CassandraDaemon\"|CMD_PATT=\"cassandra\" ${CHANGE_MARK}|g" /etc/init.d/cassandra


sleep 30
echo "$script_name: Start cassandra"
service cassandra start
