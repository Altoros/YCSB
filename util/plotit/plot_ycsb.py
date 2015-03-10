""" Plot values you gave using parse_ycsb_log.sh tool.
    As the result you'll get next images:
       latency.svg
       throughput.svg
       operations.svg
"""
import argparse
import os
import sys

import matplotlib.pyplot as plt


us_str_to_ms = lambda us: float(us)/1000


def parse_input_data(src):
    with open(src) as f:
        data = []

        for line in f.readlines():
            data.append(line.split(' '))

        return data


def plot(data=None, time_step=1):
    time_series = xrange(0, time_step*len(data), time_step)

    plot_latency(data, time_series)
    plot_throughput(data, time_series)
    plot_operations(data, time_series)


def plot_latency(data, time_series):
    latencies = map(lambda tuple: us_str_to_ms(tuple[2]), data)

    plt.xlabel('time (sec)')
    plt.ylabel('latency (ms)')

    line, = plt.plot(time_series, latencies)
    line.set_antialiased(False)

    plt.setp(line, color='r', linewidth=0.3)
    plt.savefig('latency.svg', bbox_bounds='tight')


def plot_throughput(data, time_series):
    throughput = map(lambda tuple: float(tuple[1]), data)

    plt.xlabel('time (sec)')
    plt.ylabel('throughput (ops/s)')

    line, = plt.plot(time_series, throughput)

    plt.setp(line, color='g', linewidth=0.3)
    plt.savefig('throughput.svg', bbox_bounds='tight')


def plot_operations(data, time_series):
    operations = map(lambda tuple: int(tuple[0]), data)

    plt.xlabel('time (sec)')
    plt.ylabel('operations')

    line, = plt.plot(time_series, operations)

    plt.setp(line, color='b', linewidth=0.3)
    plt.savefig('operations.svg', bbox_bounds='tight')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument("--data-file", dest="data_file", type=str, help="<operations count, throughput, latency> data file")
    parser.add_argument("--time-step", dest="time_step", type=int, help="Time step", default=1)
    args = parser.parse_args()

    if not args.data_file:
        sys.exit(0)

    if not os.path.isfile(args.data_file):
        print "Cann't read data file"
        sys.exit(1)

    plot(parse_input_data(args.data_file), args.time_step)
