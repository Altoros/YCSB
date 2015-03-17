""" Plots values you gave using parse_ycsb_log.sh tool.
    As the result you'll get graphs of latency function,
    throughput function and operations function represented
    as images or in PyPlot windows.
"""
import argparse
import os
import sys

from multiprocessing import Process

import numpy as np

from matplotlib import pyplot as plt


us_str_to_ms = lambda us: float(us)/1000


def fork_plot(plot_fn, fn_args):
    proc = Process(None, target=plot_fn, args=fn_args)
    proc.start()
    return proc


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

    fig = plt.figure()
    fig.canvas.set_window_title('Latency function')
    plt.xlabel('time (sec)')
    plt.ylabel('latency (ms)')

    plt.plot(time_series, latencies,
             label='latency',
             color='#66b032',
             linewidth=1)

    avg = round(np.average(latencies), 2)
    plt.axhline(y=avg,
                label='average=%s ms' % avg,
                color='#fe2712',
                linewidth=1)

    plt.legend()
    save_or_show_plot(plt, 'latency.svg', plot_params.display)


def plot_throughput(data, time_series, plot_params):
    throughput = map(lambda tuple: float(tuple[1]), data)

    fig = plt.figure()
    fig.canvas.set_window_title('Throughput function')
    plt.xlabel('time (sec)')
    plt.ylabel('throughput (ops/s)')

    plt.plot(time_series, throughput,
             label='throughput',
             color='#fb9902',
             linewidth=1)

    avg = round(np.average(throughput))
    plt.axhline(y=avg,
                label='average=%s ops/s' % int(avg),
                color='#0247fe',
                linewidth=1)

    plt.legend()
    save_or_show_plot(plt, 'throughput.svg', plot_params.display)


def plot_operations(data, time_series, plot_params):
    operations = map(lambda tuple: int(tuple[0]), data)

    fig = plt.figure()
    fig.canvas.set_window_title('Operations function')
    plt.xlabel('time (sec)')
    plt.ylabel('operations')

    plt.plot(time_series, operations,
             label='operations',
             color='#3d01a4',
             linewidth=1)

    save_or_show_plot(plt, 'operations.svg', plot_params.display)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument("--data-file", dest="data_file", type=str, required=True, help="<operations count, throughput, latency> data file")
    parser.add_argument("--time-step", dest="time_step", type=int, default=1, help="Time step")
    parser.add_argument('-w', dest="display", action='store_true', help="If specified data will be plotted in windows otherwise exported into files")
    args = parser.parse_args()

    return_code = plot(args)
    sys.exit(return_code)
