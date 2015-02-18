#!/bin/sh

echo "Disable transparent huge pages"
cp conf/rc.local /etc/rc.local

echo "Update blockdev"
blockdev --setra 32 /dev/sdb1
blockdev --setra 32 /dev/sda6
