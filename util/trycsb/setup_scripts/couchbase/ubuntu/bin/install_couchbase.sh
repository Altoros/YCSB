#!/bin/bash

echo "Installing couchbase"
echo "deb http://packages.couchbase.com/ubuntu trusty trusty/main" | sudo tee /etc/apt/sources.list.d/couchbase.list
curl -L http://packages.couchbase.com/ubuntu/couchbase.key | sudo apt-key add -

apt-get update
apt-get install couchbase-server