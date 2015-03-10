#!/bin/bash

if [ -z "$1" ]; then
    echo "Specify in file"
    exit 1
fi

if [ -z "$2" ]; then
    echo "Specify out file name prefix"
    exit 1
fi

in=$1
prefix=$2

cat ${in} | grep "sec:" | tee >(awk -F '[ =\\]]' '{ throughput=$6;
                                                    latency=$11;
                                                    operations=$4;

                                                    if (length(throughput) == 0)
                                                        throughput = 0;

                                                    if (length(latency) == 0)
                                                        latency = 0;
                                                    print operations, throughput, latency}' > ${prefix}_data.txt) \
                              > /dev/null
