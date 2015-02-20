#!/bin/sh

echo "Settings up sysstat"
apt-get install -y sysstat
sed -i.bak 's/ENABLED="false"/ENABLED="true"/' /etc/default/sysstat
service sysstat restart

apt-get install -y htop
apt-get install -y bwm-ng
