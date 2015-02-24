#!/bin/bash

script_name=`basename $0`
CASSANDRA_CONF_DIR=/etc/cassandra
CASSANDRA_CONF_BACKUP_DIR=${CASSANDRA_CONF_DIR}/original_bak

is_intalled_cassandra=$(dpkg-query -W -f='${Status}' dsc21 2>/dev/null | grep -c "ok installed")

if [ ${is_intalled_cassandra} -eq 1 ];
then
    echo 'Cassandra already installed'
    exit 0
fi

echo "$script_name: Installing Cassandra"
echo "deb http://debian.datastax.com/community stable main" | sudo tee -a /etc/apt/sources.list.d/cassandra.sources.list
curl -L http://debian.datastax.com/debian/repo_key | sudo apt-key add -

apt-get update
apt-get install -y --force-yes dsc21
#apt-get install -y --force-yes opscenter
#apt-get install -y --force-yes datastax-agent

echo "$script_name: Stopping Cassandra"
service cassandra stop

echo "$script_name: Backup original conf"
if [ -z "$CASSANDRA_CONF_BACKUP_DIR" ]; then
    echo "Cassandra confs backup dir unspecified"
    exit 1
fi

rm -R ${CASSANDRA_CONF_BACKUP_DIR}
mkdir -p ${CASSANDRA_CONF_BACKUP_DIR}
chown cassandra:cassandra ${CASSANDRA_CONF_BACKUP_DIR}

cp ${CASSANDRA_CONF_DIR}/*.yaml ${CASSANDRA_CONF_BACKUP_DIR}
cp ${CASSANDRA_CONF_DIR}/*.properties ${CASSANDRA_CONF_BACKUP_DIR}
cp ${CASSANDRA_CONF_DIR}/*.sh ${CASSANDRA_CONF_BACKUP_DIR}
