""" Plot values you gave using parse_ycsb_log.sh tool.
    As the result you'll get next images:
       latency.svg
       throughput.svg
       operations.svg
"""
from multiprocessing import Process

import argparse
import os
import sys

import matplotlib.pyplot as plt


us_str_to_ms = lambda us: float(us)/1000


def join_proc(proc):
    if proc:
        proc.join()


def parse_input_data(src):
    with open(src) as f:
        data = []

        for line in f.readlines():
            data.append(line.split(' '))

        return data


def validate_params(params):
    errors = []

    if not params.data_file:
        errors.append('Data file has to be specified')
    elif not os.path.isfile(params.data_file):
        errors.append('Can not read data file')

    return errors


def fork_plot(plot_fn, fn_args):
    proc = Process(None, target=plot_fn, args=fn_args)
    proc.start()
    return proc


def save_or_show_plot(plt, dest_name, is_display):
    if is_display:
        plt.show()
    else:
        plt.savefig(dest_name, bbox_bounds='tight')
        return None


def plot(params):
    errors = validate_params(params)
    if len(errors) > 0:
        for err in errors:
            print err

        return 1

    data = parse_input_data(params.data_file)

    time_series = xrange(0, params.time_step*len(data), params.time_step)

    latency_proc = fork_plot(plot_latency, (data, time_series, params))
    throughput_proc = fork_plot(plot_throughput, (data, time_series, params))
    operations_proc = fork_plot(plot_operations, (data, time_series, params))

    join_proc(latency_proc)
    join_proc(throughput_proc)
    join_proc(operations_proc)

    return 0


def plot_latency(data, time_series, plot_params):
    latencies = map(lambda tuple: us_str_to_ms(tuple[2]), data)

    plt.xlabel('time (sec)')
    plt.ylabel('latency (ms)')

    line, = plt.plot(time_series, latencies)
    line.set_antialiased(False)

    plt.setp(line, color='r', linewidth=0.3)

    save_or_show_plot(plt, 'latency.svg', plot_params.display)


def plot_throughput(data, time_series, plot_params):
    throughput = map(lambda tuple: float(tuple[1]), data)

    plt.xlabel('time (sec)')
    plt.ylabel('throughput (ops/s)')

    line, = plt.plot(time_series, throughput)

    plt.setp(line, color='g', linewidth=0.3)

    save_or_show_plot(plt, 'throughput.svg', plot_params.display)


def plot_operations(data, time_series, plot_params):
    operations = map(lambda tuple: int(tuple[0]), data)

    plt.xlabel('time (sec)')
    plt.ylabel('operations')

    line, = plt.plot(time_series, operations)

    plt.setp(line, color='b', linewidth=0.3)

    save_or_show_plot(plt, 'operations.svg', plot_params.display)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument("--data-file", dest="data_file", type=str, help="<operations count, throughput, latency> data file")
    parser.add_argument("--time-step", dest="time_step", type=int, default=1, help="Time step")
    parser.add_argument('-w', dest="display", action='store_true', help="If specified data will be plotted in windows otherwise exported into files")
    args = parser.parse_args()

    return_code = plot(args)
    sys.exit(return_code)
