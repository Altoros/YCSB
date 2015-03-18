#!/bin/sh

releasever=6
echo "[mongodb-org-3.0]
name=MongoDB Repository
baseurl=http://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/testing/x86_64/
gpgcheck=0
enabled=1" | sudo tee /etc/yum.repos.d/mongodb-org-3.0.repo
yum install -y mongodb-org-mongos mongodb-org-shell
