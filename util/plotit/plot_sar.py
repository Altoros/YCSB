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


def get_stats(stats_src, stats_names):
    stats = {}

    with open(stats_src) as f:
        data = f.readlines()

        names = data[0].strip().split(';')
        for name in names:
            stats[name] = []

        for line in data[1:]:
            line_points = line.split(';')
            [stats[x].append(y) for (x, y) in zip(names, line_points)]

    return {key: stats[key] for key in stats_names}


def plot_any_system_stats(src_sar_log_path, sar_system_flag,
                          stats_names, tmp_stats_file_name, plot_title):
    stats_out = '%s_stats.tmp' % tmp_stats_file_name
    os.system('sadf -d %s -- %s > %s' % (src_sar_log_path, sar_system_flag, stats_out))

    stats = get_stats(stats_out, stats_names)
    time = range( len(stats[stats.keys()[0]]) )

    def get_show_hide_fn(stats_lines):
        def fn(checkbox_label):
            line = stats_lines[checkbox_label]
            line.set_visible(not line.get_visible())
            plt.draw()

        return fn

    def do_plot():
        fig, ax = plt.subplots()
        fig.canvas.set_window_title(plot_title)
        plt.xlabel('time (sec)')

        stats_lines = {}
        for key in stats.keys():
            l, = ax.plot(time, stats[key], label=key, lw=1)
            stats_lines[key] = l

        rax = plt.axes([0.01, 0.8, 0.1, 0.1])
        check = CheckButtons(rax, stats_names, [True] * len(stats_names))
        check.on_clicked(get_show_hide_fn(stats_lines))

        ax.legend()
        plt.subplots_adjust(left=0.2)
        plt.show()

    do_plot()


def plot_cpu_stats(params):
    stats_names = ['%user', '%nice', '%system', '%iowait']
    plot_any_system_stats(params.sar_log, '-u', stats_names, 'cpu_stats', 'CPU activity (all cores)')


def plot_ram_stats_in_kb(params):
    stats_names = ['kbmemfree', 'kbmemused', 'kbbuffers', 'kbcached', 'kbcommit', 'kbactive', 'kbinact', 'kbdirty']
    plot_any_system_stats(params.sar_log, '-r', stats_names, 'ram_kb_stats', 'Memory activity (kilobytes)')


def plot_ram_stats_in_percents(params):
    stats_names = ['%memused', '%commit']
    plot_any_system_stats(params.sar_log, '-r', stats_names, 'ram_percents_stats', 'Memory activity (percents)')


def plot_disk_stats(params):
    stats_names = ['tps', 'rtps', 'wtps', 'bread/s', 'bwrtn/s']
    plot_any_system_stats(params.sar_log, '-d -p', stats_names, 'dsk_stats', 'Disks activity')


def plot_queue_stats(params):
    stats_names = ['runq-sz', 'plist-sz', 'blocked']
    plot_any_system_stats(params.sar_log, '-q', stats_names, 'queue_stats', 'Queue activity')


def plot_network_stats(params):
    stats_names = ['rxkB/s', 'txkB/s', '%ifutil']
    plot_any_system_stats(params.sar_log, '-n DEV', stats_names, 'network_stats', 'Network activity')


def plot_stats(params):
    cpu_proc  = fork_plot(plot_cpu_stats, (params, ))
    ram_proc0 = fork_plot(plot_ram_stats_in_kb, (params, ))
    ram_proc1 = fork_plot(plot_ram_stats_in_percents, (params, ))
    dsk_proc  = fork_plot(plot_disk_stats, (params, ))
    queue_proc = fork_plot(plot_queue_stats, (params, ))
    network_proc = fork_plot(plot_network_stats, (params, ))

    join_proc(cpu_proc)
    join_proc(ram_proc0)
    join_proc(ram_proc1)
    join_proc(dsk_proc)
    join_proc(queue_proc)
    join_proc(network_proc)

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument('--sar_log', type=str, required=True, help='SAR log filename')
    args = parser.parse_args()

    return_code = plot_stats(args)
    sys.exit(return_code)

