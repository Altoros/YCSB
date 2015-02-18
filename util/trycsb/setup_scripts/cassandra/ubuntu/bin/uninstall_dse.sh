#!/bin/bash

echo 'Uninstalling Cassandra'

dpkg --configure -a

service cassandra stop

rm /etc/apt/sources.list.d/cassandra.sources.list
rm -R /etc/cassandra
apt-get remove -y --purge dsc21
apt-get remove -y --purge opscenter
apt-get -y --purge autoremove