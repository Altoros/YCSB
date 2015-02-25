#!/bin/bash

echo "Uninstalling Couchbase"
service couchbase-server stop
dpkg -r couchbase-server
rm -R /opt/couchbase