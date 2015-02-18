#!/bin/sh

echo "Settings up java 1.7"
apt-get install -y software-properties-common
apt-add-repository -y ppa:webupd8team/java
apt-get update
apt-get install -y debconf-utils
echo debconf shared/accepted-oracle-license-v1-1 select true | debconf-set-selections
echo debconf shared/accepted-oracle-license-v1-1 seen true | debconf-set-selections
apt-get install -y oracle-java7-installer
apt-get install -y oracle-java7-set-default
