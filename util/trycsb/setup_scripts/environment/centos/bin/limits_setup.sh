#!/bin/bash

echo "Replace /etc/sysctl.conf"
cp conf/sysctl.conf /etc/sysctl.conf

echo "Replace /etc/security/limits.conf"
cp conf/limits.conf /etc/security/limits.conf

echo "Replace /etc/security/limits.d/90-nproc.conf"
cp conf/90-nproc.conf /etc/security/limits.d/90-nproc.conf

echo "Print sysctl -p"
sysctl -p
