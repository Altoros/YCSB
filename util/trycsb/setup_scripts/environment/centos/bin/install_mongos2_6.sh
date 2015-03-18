#!/bin/sh

echo "[mongodb-org-2.6]
name=MongoDB 2.6 Repository
baseurl=http://downloads-distro.mongodb.org/repo/redhat/os/x86_64/
gpgcheck=0
enabled=1" | sudo tee /etc/yum.repos.d/mongodb-org-2.6.repo
yum install -y mongodb-org-mongos mongodb-org-shell
