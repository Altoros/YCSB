#!/bin/sh

if [ -z "$1" ]; then
    echo "Host address required"
    exit 1
fi

CURRENT_HOST_ADDR=$1
MONGODB_DATA=/disk1/mongodb-data
MONGODB_LOGS=/disk1/mongodb-logs
MONGODB_CONF_DIR=/disk1/mongodb-conf
MONGODB_CONF=$MONGODB_CONF_DIR/mongodb-config.yaml
MONGODB_JOURNAL_DIR=/mongodb-journal

MONGOD_UPSTART_SOURCE=conf/upstart.conf
MONGOD_UPSTART_TARGET=/etc/init/mongod-rs

declare -A SHARDS
SHARDS['50.23.195.162']="shard00-mongod.yaml shard02-mongod.yaml"
SHARDS['192.155.206.162']="shard10-mongod.yaml shard11-mongod.yaml"
SHARDS['192.155.206.163']="shard21-mongod.yaml shard22-mongod.yaml"

mkdir -p $MONGODB_CONF_DIR
mkdir -p $MONGODB_DATA
mkdir -p $MONGODB_LOGS
mkdir -p $MONGODB_JOURNAL_DIR

IFS=" "
read -a MONGODS <<< ${SHARDS[$CURRENT_HOST_ADDR]}

REPLICA_SET_INDEX=0
for MONGOD in ${MONGODS[*]}
do
    echo "prepare a replica set #" $REPLICA_SET_INDEX
    replica_set_path=$MONGODB_DATA/db/rs$REPLICA_SET_INDEX
    mkdir -p $replica_set_path
    cp conf/$MONGOD $MONGODB_CONF_DIR
    echo "link journal on external drive"
    mkdir -p $MONGODB_JOURNAL_DIR/rs$REPLICA_SET_INDEX/journal
    ln -s -f $MONGODB_JOURNAL_DIR/rs$REPLICA_SET_INDEX/journal $replica_set_path/journal
    # overwrite default upstart script
    cp $MONGOD_UPSTART_SOURCE $MONGOD_UPSTART_TARGET$REPLICA_SET_INDEX.conf
    sed -i "s|CONF=\/etc\/mongod.conf|CONF=$MONGODB_CONF_DIR\/$MONGOD|g" $MONGOD_UPSTART_TARGET$REPLICA_SET_INDEX.conf
    let REPLICA_SET_INDEX=REPLICA_SET_INDEX+1
done

# config server settings
mkdir -p $MONGODB_DATA/config
cp conf/mongod-config.yaml $MONGODB_CONF
cp $MONGOD_UPSTART_SOURCE $MONGOD_UPSTART_TARGET-config.conf
sed -i "s|bindIp:|bindIp: $CURRENT_HOST_ADDR|g" $MONGODB_CONF
sed -i "s|CONF=\/etc\/mongod.conf|CONF=$MONGODB_CONF|g" $MONGOD_UPSTART_TARGET-config.conf

chown -R mongodb:mongodb $MONGODB_DATA
chown -R mongodb:mongodb $MONGODB_CONF_DIR
chown -R mongodb:mongodb $MONGODB_LOGS
chown -R mongodb:mongodb $MONGODB_JOURNAL_DIR




