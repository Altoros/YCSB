#!/bin/sh

echo "Uninstalling mongodb"
apt-key del 7F0CEB10
rm /etc/apt/sources.list.d/mongodb.list
apt-get remove -y --purge mongodb-org
# if running on NUMA machine
echo "Uninstalling numactl"
apt-get remove -y --purge numactl
apt-get -y --purge autoremove
