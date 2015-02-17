#!/bin/bash

echo "replace /etc/sysctl.conf"
cp conf/sysctl.conf /etc/sysctl.conf

echo "replace /etc/security/limits.conf"
cp conf/limits.conf /etc/security/limits.conf

sysctl -p

echo "replace /etc/fstab"
cp conf/limits.conf /etc/security/limits.conf