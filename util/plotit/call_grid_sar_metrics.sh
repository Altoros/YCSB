#!/bin/bash

if [ -z "$1" ]; then
    echo "Summary metrics src dir name missed" >&2
    exit 1
fi

if [ -z "$2" ]; then
    echo "Summary matrix out file name missed" >&2
    exit 1
fi

metrics1_prefix="sysstat_192.155.206.162_metrics_summary_"
metrics2_prefix="sysstat_192.155.206.163_metrics_summary_"
metrics3_prefix="sysstat_50.23.195.162_metrics_summary_"

cpu_metrics_postfix="CPU_[all_cores].txt"
ram_metrics_postfix="RAM.txt"
sda_metrics_postfix="Disk_[sda].txt"
sdb_metrics_postfix="Disk_[sdb].txt"
net13_metrics_postfix="Network_[eth3].txt"
net2_metrics_postfix="Network_[eth5].txt"

cmd_line="-cpu ${metrics1_prefix}${cpu_metrics_postfix},${metrics2_prefix}${cpu_metrics_postfix},${metrics3_prefix}${cpu_metrics_postfix}
          -ram ${metrics1_prefix}${ram_metrics_postfix},${metrics2_prefix}${ram_metrics_postfix},${metrics3_prefix}${ram_metrics_postfix}
          -net ${metrics1_prefix}${net13_metrics_postfix},${metrics2_prefix}${net2_metrics_postfix},${metrics3_prefix}${net13_metrics_postfix}
          -dsk_sda ${metrics1_prefix}${sda_metrics_postfix},${metrics2_prefix}${sda_metrics_postfix},${metrics3_prefix}${sda_metrics_postfix}
          -dsk_sdb ${metrics1_prefix}${sdb_metrics_postfix},${metrics2_prefix}${sdb_metrics_postfix},${metrics3_prefix}${sdb_metrics_postfix}
          -in_dir ${1}
          -out ${2}
          --"

bash grid_sar_metrics.sh ${cmd_line}