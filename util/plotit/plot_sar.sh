#!/bin/bash

../plot_sar.py -s stats1 -p cpu ram dsk net -d sda sdb -i eth3 --export-prefix=stats1_
../plot_sar.py -s stats2 -p cpu ram dsk net -d sda sdb -i eth5 --export-prefix=stats2_
../plot_sar.py -s stats3 -p cpu ram dsk net -d sda sdb -i eth3 --export-prefix=stats3_
