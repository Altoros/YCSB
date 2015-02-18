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
SEEDS="10.62.53.132"

declare -A LOCAL_ADDRESSES
LOCAL_ADDRESSES['50.97.182.67']="10.62.53.132"
LOCAL_ADDRESSES['50.97.182.68']="10.62.53.134"
LOCAL_ADDRESSES['50.97.182.69']="10.62.53.136"

declare -A TOKENS
TOKENS['50.97.182.67']="-9223372036854775808"
TOKENS['50.97.182.68']="-3074457345618258603"
TOKENS['50.97.182.69']="3074457345618258602"


rm -R /var/log/cassandra/*


echo "Create directories"
mkdir -p $CASSANDRA_COMMITLOG_DIR
rm -R $CASSANDRA_COMMITLOG_DIR/*
chown cassandra:cassandra $CASSANDRA_COMMITLOG_DIR

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

