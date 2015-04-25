#!/bin/bash

echo "Uninstalling Couchbase"
service couchbase-server stop
dpkg -r couchbase-server
#rm -R /opt/couchbase
#rm -R /opt/couchbase/var/lib/couchbase/data /disk1/couchbase/index