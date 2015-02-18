#!/bin/bash

CASSANDRA_CONF_DIR=/etc/cassandra

is_intalled_cassandra=$(dpkg-query -W -f='${Status}' dsc21 2>/dev/null | grep -c "ok installed")

if [ $is_intalled_cassandra -eq 1 ];
then
    echo 'Cassandra already installed'
    exit 0
fi

echo 'Installing Cassandra'
echo "deb http://debian.datastax.com/community stable main" | sudo tee -a /etc/apt/sources.list.d/cassandra.sources.list
curl -L http://debian.datastax.com/debian/repo_key | sudo apt-key add -

apt-get update
apt-get install -y --force-yes dsc21
apt-get install -y --force-yes opscenter

cp $CASSANDRA_CONF_DIR/cassandra.yaml $CASSANDRA_CONF_DIR/cassandra.orig.yaml
cp $CASSANDRA_CONF_DIR/cassandra-topology.properties $CASSANDRA_CONF_DIR/cassandra-topology.orig.properties