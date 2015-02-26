#!/bin/bash

echo "Uninstalling Couchbase"
service couchbase-server stop
dpkg -r couchbase-server
rm -R /opt/couchbase
#TODO $rm -R $COUCHBASE_DATA_PATH and $COUCHBASE_INDEX_PATH