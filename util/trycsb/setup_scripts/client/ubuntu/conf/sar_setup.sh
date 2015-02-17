#!/bin/sh

apt-get install sysstat
sed -i.bak 's/ENABLED="false"/ENABLED="true"/' /etc/default/sysstat
service sysstat restart
