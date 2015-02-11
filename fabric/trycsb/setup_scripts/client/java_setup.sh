#!/bin/sh

sudo apt-get install software-properties-common
sudo apt-add-repository -y ppa:webupd8team/java
sudo apt-get update
sudo apt-get install debconf-utils
sudo echo debconf shared/accepted-oracle-license-v1-1 select true | debconf-set-selections
sudo echo debconf shared/accepted-oracle-license-v1-1 seen true | debconf-set-selections
sudo apt-get install oracle-java7-installer
sudo apt-get install oracle-java7-set-default
