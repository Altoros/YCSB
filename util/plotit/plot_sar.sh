#!/bin/bash

if [ -z "$1" ]; then
    echo "Logs dir missed" >&2
    exit 1
fi

echo "STARTED: ${1}/sysstat_192.155.206.162.log"
python plot_sar.py -s ${1}/sysstat_192.155.206.162.log -p cpu ram dsk net -d sda sdb -i eth3 --export-prefix=sysstat_192.155.206.162_ --export-dir=${1}/analysed
echo "DONE: ${1}/sysstat_192.155.206.162.log"
echo

echo "STARTED: ${1}/sysstat_192.155.206.163.log"
python plot_sar.py -s ${1}/sysstat_192.155.206.163.log -p cpu ram dsk net -d sda sdb -i eth5 --export-prefix=sysstat_192.155.206.163_ --export-dir=${1}/analysed
echo "DONE: ${1}/sysstat_192.155.206.163.log"
echo

echo "STARTED: ${1}/sysstat_50.23.195.162.log "
python plot_sar.py -s ${1}/sysstat_50.23.195.162.log -p cpu ram dsk net -d sda sdb -i eth3 --export-prefix=sysstat_50.23.195.162_ --export-dir=${1}/analysed
echo "DONE: ${1}/sysstat_50.23.195.162.log"
echo

echo "STARTED: metrics_summary_matrix"
bash call_grid_sar_metrics.sh ${1}/analysed metrics_summary_matrix.txt
echo "DONE: metrics_summary_matrix"