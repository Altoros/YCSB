#!/bin/sh

if [ -z "$1" ]; then
    echo "Host address required"
    exit 1
fi

CURRENT_HOST_ADDR=$1
MONGODB_DATA=/disk1/mongodb-data
MONGODB_LOGS=/disk1/mongodb-logs
MONGODB_CONF_DIR=/disk1/mongodb-conf

MONGOD_UPSTART_SOURCE=conf/upstart.conf
MONGOD_UPSTART_TARGET=/etc/init/mongod-rs

declare -A SHARDS
SHARDS['50.23.195.162']="shard00-mongod.yaml shard02-mongod.yaml"
SHARDS['192.155.206.162']="shard10-mongod.yaml shard11-mongod.yaml"
SHARDS['192.155.206.163']="shard21-mongod.yaml shard22-mongod.yaml"

mkdir -p $MONGODB_CONF_DIR
mkdir -p $MONGODB_DATA
mkdir -p $MONGODB_LOGS

IFS=" "
read -a MONGODS <<< ${SHARDS[$CURRENT_HOST_ADDR]}

REPLICA_SET_INDEX=0
for MONGOD in ${MONGODS[*]}
do
    echo "prepare a replica set #" $REPLICA_SET_INDEX
    mkdir -p $MONGODB_DATA/db/rs$REPLICA_SET_INDEX
    cp conf/$MONGOD $MONGODB_CONF_DIR
    # overwrite default upstart script
    cp $MONGOD_UPSTART_SOURCE $MONGOD_UPSTART_TARGET$REPLICA_SET_INDEX.conf
    sed -i "s|CONF=\/etc\/mongod.conf|CONF=$MONGODB_CONF_DIR\/$MONGOD|g" $MONGOD_UPSTART_TARGET$REPLICA_SET_INDEX.conf
    let REPLICA_SET_INDEX=REPLICA_SET_INDEX+1
done

mkdir -p $MONGODB_DATA/config
cp conf/mongod-config.yaml $MONGODB_CONF_DIR
cp $MONGOD_UPSTART_SOURCE $MONGOD_UPSTART_TARGET-config.conf
sed -i "s|bindIp:|bindIp: $CURRENT_HOST_ADDR|g" $MONGODB_CONF_DIR/mongod-config.yaml
sed -i "s|CONF=\/etc\/mongod.conf|CONF=$MONGODB_CONF_DIR\/mongod-config.yaml|g" $MONGOD_UPSTART_TARGET-config.conf

chown -R mongodb:mongodb $MONGODB_DATA
chown -R mongodb:mongodb $MONGODB_CONF_DIR
chown -R mongodb:mongodb $MONGODB_LOGS




