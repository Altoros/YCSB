#!/bin/sh

curl -O http://downloads.mongodb.org/linux/mongodb-linux-x86_64-2.6.7.tgz
tar -xvf mongodb-linux-x86_64-2.6.7.tgz
export PATH=$PATH:~/mongodb-linux-x86_64-2.6.7/bin
