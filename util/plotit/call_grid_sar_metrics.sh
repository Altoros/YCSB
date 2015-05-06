#!/bin/bash

metrics1_prefix="stats1_metrics_summary_"
metrics2_prefix="stats2_metrics_summary_"
metrics3_prefix="stats3_metrics_summary_"

cpu_metrics_postfix="CPU_activity_[all_cores].txt"
ram_metrics_postfix="Memory_activity.txt"
sda_metrics_postfix="Disk_[sda]_activity.txt"
sdb_metrics_postfix="Disk_[sda]_activity.txt"
net13_metrics_postfix="Network_[eth3]_activity.txt"
net2_metrics_postfix="Network_[eth5]_activity.txt"

cmd_line="-cpu ${metrics1_prefix}${cpu_metrics_postfix},${metrics2_prefix}${cpu_metrics_postfix},${metrics3_prefix}${cpu_metrics_postfix}
          -ram ${metrics1_prefix}${ram_metrics_postfix},${metrics2_prefix}${ram_metrics_postfix},${metrics3_prefix}${ram_metrics_postfix}
          -net ${metrics1_prefix}${net13_metrics_postfix},${metrics2_prefix}${net2_metrics_postfix},${metrics3_prefix}${net13_metrics_postfix}
          -dsk_sda ${metrics1_prefix}${sda_metrics_postfix},${metrics2_prefix}${sda_metrics_postfix},${metrics3_prefix}${sda_metrics_postfix}
          -dsk_sdb ${metrics1_prefix}${sdb_metrics_postfix},${metrics2_prefix}${sdb_metrics_postfix},${metrics3_prefix}${sdb_metrics_postfix}
          --"

../grid_sar_metrics.sh ${cmd_line}