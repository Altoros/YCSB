#!/bin/bash

echo 'Uninstalling Couchbase'

service couchbase-server stop
# sudo /etc/init.d/couchbase-server stop

rm -R /opt/couchbase
dpkg -r couchbase-server