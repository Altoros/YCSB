#!/bin/sh

sudo apt-get install sysstat
sudo sed -i.bak 's/ENABLED="false"/ENABLED="true"/' /etc/default/sysstat
sudo service sysstat restart
