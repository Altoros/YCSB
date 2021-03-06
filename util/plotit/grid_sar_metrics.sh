#!/bin/bash

if [ -z "$1" ]; then
    echo "Specify metrics file(s)" >&2
    exit 1
fi

cpu_metrics_in_set=""
ram_metrics_in_set=""
sda_metrics_in_set=""
sdb_metrics_in_set=""
net_metrics_in_set=""

while true; do
    case "$1" in
        -cpu)
            cpu_metrics_in_set="${2//,/ }"
            shift 2
        ;;
        -ram)
            ram_metrics_in_set="${2//,/ }"
            shift 2
        ;;
        -dsk_sda)
            sda_metrics_in_set="${2//,/ }"
            shift 2
        ;;
        -dsk_sdb)
            sdb_metrics_in_set="${2//,/ }"
            shift 2
        ;;
        -net)
            net_metrics_in_set="${2//,/ }"
            shift 2
        ;;
        -in_dir)
            input_dir_name="${2}"
            shift 2
        ;;
        -out)
            output_file_name="${2}"
            shift 2
        ;;
        --)
            shift
            break
        ;;
        *)
            echo "Error parsing arguments starting with $1!" >&2
            exit 1
        ;;
    esac
done

cd ${input_dir_name}

echo `pwd`
echo "Metrics files to be parsed:"
echo ${sda_metrics_in_set}
echo ${sdb_metrics_in_set}
echo ${ram_metrics_in_set}
echo ${cpu_metrics_in_set}
echo ${net_metrics_in_set}

echo "Output lines contains next metrics:
1  sda rd_sec_s
2  sda wr_sec_s
3  sda await
4  sda %util
5  sdb rd_sec_s
6  sdb wr_sec_s
7  sdb await
8  sdb %util
9  ram kbmemused
10 ram kbcached
11 ram kbcommit
12 cpu %user
13 cpu %iowait
14 net rxkB_s
15 net txkB_s
"

out=${output_file_name}

grep rd_sec_s ${sda_metrics_in_set} | awk -F '[=]' '{ printf "%s\t", $2; }' >> ${out} && echo >> ${out}
grep wr_sec_s ${sda_metrics_in_set} | awk -F '[=]' '{ printf "%s\t", $2; }' >> ${out} && echo >> ${out}
grep await ${sda_metrics_in_set} | awk -F '[=]' '{ printf "%s\t", $2; }' >> ${out} && echo >> ${out}
grep %util ${sda_metrics_in_set} | awk -F '[=]' '{ printf "%s\t", $2; }' >> ${out} && echo >> ${out}

grep rd_sec_s ${sdb_metrics_in_set} | awk -F '[=]' '{ printf "%s\t", $2; }' >> ${out} && echo >> ${out}
grep wr_sec_s ${sdb_metrics_in_set} | awk -F '[=]' '{ printf "%s\t", $2; }' >> ${out} && echo >> ${out}
grep await ${sdb_metrics_in_set} | awk -F '[=]' '{ printf "%s\t", $2; }' >> ${out} && echo >> ${out}
grep %util ${sdb_metrics_in_set} | awk -F '[=]' '{ printf "%s\t", $2; }' >> ${out} && echo >> ${out}

grep kbmemused ${ram_metrics_in_set} | awk -F '[=]' '{ printf "%s\t", $2; }' >> ${out} && echo >> ${out}
grep kbcached ${ram_metrics_in_set} | awk -F '[=]' '{ printf "%s\t", $2; }' >> ${out} && echo >> ${out}
grep kbcommit ${ram_metrics_in_set} | awk -F '[=]' '{ printf "%s\t", $2; }' >> ${out} && echo >> ${out}

grep %user ${cpu_metrics_in_set} | awk -F '[=]' '{ printf "%s\t", $2; }' >> ${out} && echo >> ${out}
grep %iowait ${cpu_metrics_in_set} | awk -F '[=]' '{ printf "%s\t", $2; }' >> ${out} && echo >> ${out}

grep rxkB_s ${net_metrics_in_set} | awk -F '[=]' '{ printf "%s\t", $2; }' >> ${out} && echo >> ${out}
grep txkB_s ${net_metrics_in_set} | awk -F '[=]' '{ printf "%s\t", $2; }' >> ${out} && echo >> ${out}

xclip -i ${out} -selection c