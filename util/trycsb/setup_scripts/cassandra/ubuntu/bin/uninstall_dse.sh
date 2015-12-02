#!/bin/bash

script_name=`basename $0`
echo "$script_name: Uninstalling Cassandra"

dpkg --configure -a

service cassandra stop

apt-get remove -y --purge cassandra
rm -rf /etc/apt/sources.list.d/cassandra.sources.list
rm -Rf /etc/cassandra
apt-get remove -y --purge dsc$1
apt-get remove -y --purge opscenter
apt-get -y --purge autoremove

