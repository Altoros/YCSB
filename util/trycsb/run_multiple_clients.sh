#!/bin/bash

script_name=`basename $0`
clients_count=${1}
workload_name=${2}
db_profile=${3}

if [ -z "$clients_count"  ];
then
    clients_count=1
fi

if [ -z "$workload_name"  ];
then
    echo "Specify workload name"
    exit 1
fi

if [ -z "$db_profile"  ];
then
    echo "Specify db profile"
    exit 1
fi

for i in `seq 1 $clients_count`;
do
    fab benchmark_run:workload_name=${workload_name}_${i},db_profile=${db_profile} > "${workload_name}_${i}.log" 2>&1 &
done
