__author__ = 'vladimir.starostenkov'

import argparse
import os
import sys

from multiprocessing import Process
from matplotlib import pyplot as plt
from matplotlib.widgets import CheckButtons


def fork_plot(plot_fn, fn_args):
    proc = Process(None, target=plot_fn, args=fn_args)
    proc.start()
    return proc


def join_proc(proc):
    if proc:
        proc.join()


def create_metrics_checkboxes(lines, metrics_names):
    ax = plt.gca()
    check = CheckButtons(ax, metrics_names, [True] * len(metrics_names))

    metric_to_line = dict(zip(metrics_names, lines))

    def show_hide_line(metric):
        line = metric_to_line[metric]
        line.set_visible(not line.get_visible())
        plt.draw()

    check.on_clicked(show_hide_line)


def get_metrics(metrics_src, metrics_names):
    metrics = {}

    with open(metrics_src) as f:
        data = f.readlines()

        names = data[0].strip().split(';')
        for name in names:
            metrics[name] = []

        for line in data[1:]:
            line_points = line.split(';')
            [metrics[x].append(y) for (x, y) in zip(names, line_points)]

    return {key: metrics[key] for key in metrics_names}


def plot_subsystem(filename, susbystem_sar_arg, metrics_to_plot, tmp_metrics_file_name):
    metrics_out = '%s_metrics.tmp' % tmp_metrics_file_name
    os.system('sadf -d %s -- %s > %s' % (filename, susbystem_sar_arg, metrics_out))

    metrics = get_metrics(metrics_out, metrics_to_plot)
    time = range( len(metrics[metrics.keys()[0]]) )

    lines = []
    for key in metrics.keys():
        line, = plt.plot(time, metrics[key], label=key, linewidth=1)
        lines.append(line)

    return lines


def plot_cpu_metrics(params):
    fig = plt.figure()
    fig.canvas.set_window_title('CPU activity (all cores)')

    metrics_names = ['%user', '%nice', '%system', '%iowait', '%steal']
    lines = plot_subsystem(params.sar_log, ' ', metrics_names, 'cpu_metrics')

    #create_metrics_checkboxes(lines, metrics_names)
    plt.legend()
    plt.show()


def plot_ram_metrics(params):
    fig = plt.figure()
    fig.canvas.set_window_title('Memory activity')

    metrics_names = ['kbmemfree', 'kbmemused', '%memused', 'kbbuffers', 'kbcached',
                     'kbcommit', '%commit', 'kbactive', 'kbinact', 'kbdirty']
    lines = plot_subsystem(params.sar_log, '-r', metrics_names, 'ram_metrics')

    #create_metrics_checkboxes(lines, metrics_names)
    plt.legend()
    plt.show()


def plot_disk_metrics(params):
    fig = plt.figure()
    fig.canvas.set_window_title('Disks activity')

    metrics_names = ['tps', 'rtps', 'wtps', 'bread/s', 'bwrtn/s']
    lines = plot_subsystem(params.sar_log, '-b', metrics_names, 'dsk_metrics')

    #create_metrics_checkboxes(lines, metrics_names)
    plt.legend()
    plt.show()


def plot_metrics(params):
    cpu_proc = fork_plot(plot_cpu_metrics, (params, ))
    ram_proc = fork_plot(plot_ram_metrics, (params, ))
    dsk_proc = fork_plot(plot_disk_metrics, (params, ))

    join_proc(cpu_proc)
    join_proc(ram_proc)
    join_proc(dsk_proc)

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument('--sar_log', type=str, required=True, help='SAR log filename')
    args = parser.parse_args()

    return_code = plot_metrics(args)
    sys.exit(return_code)

