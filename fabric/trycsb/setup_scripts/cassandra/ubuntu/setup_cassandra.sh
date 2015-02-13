#!/bin/bash

if [ -z "$1" ]; then
    echo "Host address required"
    exit 1
fi

CURRENT_HOST_ADDR=$1

echo "deb http://sergey.sintsov_altoros.com:t0VnpFpQS70Jtf0@debian.datastax.com/enterprise stable main" | sudo tee -a /etc/apt/sources.list.d/datastax.sources.list
curl -L https://debian.datastax.com/debian/repo_key | sudo apt-key add -
apt-get update
apt-get install dse-full
apt-get install opscenter

mkdir -p /disk1/cassandra-commitlog
chown cassandra:cassandra /disk1/cassandra-commitlog

mkdir -p /var/cassandra-data
chown cassandra:cassandra /var/cassandra-data

cp conf/cassandra.yaml /etc/dse/cassandra/cassandra.yaml
cp conf/cassandra-topology.yaml /etc/dse/cassandra/cassandra-topology.yaml
cp conf/cassandra-env.sh /etc/dse/cassandra/cassandra-env.sh


declare -A tokens
tokens['50.97.182.67']="-9223372036854775808"
tokens['50.97.182.68']="-3074457345618258603"
tokens['50.97.182.69']="3074457345618258602"

sed -i.sed.bak "s|initial_token: 0|initial_token: '${tokens[$CURRENT_HOST_ADDR]}'|g" /etc/dse/cassandra/cassandra.yaml