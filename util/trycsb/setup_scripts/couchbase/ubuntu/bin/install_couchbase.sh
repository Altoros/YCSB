#!/bin/bash

echo "Installing Couchbase"
wget http://packages.couchbase.com/releases/3.0.2/couchbase-server-enterprise_3.0.2-ubuntu12.04_amd64.deb
dpkg -i couchbase-server-enterprise_3.0.2-ubuntu12.04_amd64.deb
sleep 10