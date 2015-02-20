#!/bin/bash

if [ -z "$1" ]; then
    echo "Host address required"
    exit 1
fi


CHANGE_MARK="# changed"
CURRENT_HOST_ADDR=$1
CASSANDRA_CONF_DIR=/etc/cassandra
CASSANDRA_CONF=$CASSANDRA_CONF_DIR/cassandra.yaml
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


rm -R /var/log/cassandra/*


echo "Create/clear $CASSANDRA_COMMITLOG_DIR"
if [ -z "$CASSANDRA_COMMITLOG_DIR" ]; then
    echo "Cassandra commitlog dir unspecified"
    exit 1
fi

mkdir -p $CASSANDRA_COMMITLOG_DIR
rm -R $CASSANDRA_COMMITLOG_DIR/*
chown cassandra:cassandra $CASSANDRA_COMMITLOG_DIR

echo "Create/clear $CASSANDRA_DATA_DIR"
if [ -z "$CASSANDRA_DATA_DIR" ]; then
    echo "Cassandra data dir unspecified"
    exit 1
fi

mkdir -p $CASSANDRA_DATA_DIR
rm -R $CASSANDRA_DATA_DIR/*
chown cassandra:cassandra $CASSANDRA_DATA_DIR


echo "Replace cassandra configs"
cp conf/cassandra-topology.properties $CASSANDRA_CONF_DIR/cassandra-topology.properties

echo "Change config settings"
sed -i "s|num_tokens: 256|num_tokens: $CHANGE_MARK|g" $CASSANDRA_CONF
sed -i "s|# initial_token:|initial_token: ${TOKENS[$CURRENT_HOST_ADDR]} $CHANGE_MARK|g" $CASSANDRA_CONF
sed -i "s|- seeds: \"127.0.0.1\"|- seeds: \"$SEEDS\" $CHANGE_MARK|g" $CASSANDRA_CONF
sed -i "s|- /var/lib/cassandra/data|- $CASSANDRA_DATA_DIR $CHANGE_MARK|g" $CASSANDRA_CONF
sed -i "s|commitlog_directory: /var/lib/cassandra/commitlog|commitlog_directory: $CASSANDRA_COMMITLOG_DIR $CHANGE_MARK|g" $CASSANDRA_CONF
sed -i "s|listen_address: localhost|listen_address: ${LOCAL_ADDRESSES[$CURRENT_HOST_ADDR]} $CHANGE_MARK|g" $CASSANDRA_CONF
sed -i "s|rpc_address: localhost|rpc_address: $CURRENT_HOST_ADDR $CHANGE_MARK|g" $CASSANDRA_CONF

