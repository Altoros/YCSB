#!/bin/bash

echo 'node initialization'
#couchbase-cli node-init -c 192.155.206.162:8091 --node-init-data-path=/tmp/data --node-init-index-path=/tmp/index -u altoros -p changeme

echo 'cluster initialization'
#couchbase-cli cluster-init -c 192.155.206.162:8091 --cluster-username=altoros --cluster-password=changeme --cluster-ramsize=1000

echo 'create bucket'
#couchbase-cli bucket-create -c 192.155.206.162:8091 --bucket=default --bucket-type=couchbase --bucket-ramsize=200 -u altoros -p changeme

echo 'add nodes to cluster'
#couchbase-cli server-add -c 192.155.206.162:8091 --server-add=192.155.206.163:8091 -u altoros -p changeme
#couchbase-cli server-add -c 192.155.206.162:8091 --server-add=50.23.195.162:8091 -u altoros -p changeme

echo 'list servers in cluster'
#couchbase-cli server-list --cluster=192.155.206.162:8091

echo 'Server information'
#couchbase-cli server-info -c 192.155.206.162:8091 -u altoros -p changeme