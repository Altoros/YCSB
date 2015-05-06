#!/usr/bin/env python

""" Plots statictics collected by sar.
"""
import argparse
import sys
import subprocess
import os
import numpy

from cached_property import cached_property

from multiprocessing import Process
from matplotlib import pyplot as plt

from common import *


class SarLogStatistics(object):

    def __init__(self, stats_src):
        self._stats_src = stats_src

    @cached_property
    def metrics_info(self):
        raise NotImplementedError('Please Implement this method')

    def _get_sar_system_flag(self):
        raise NotImplementedError('Please Implement this method')

    def _read_sar_statistics(self):
        cmd = 'sadf -d %s -- %s' % (self._stats_src, self._get_sar_system_flag())

        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        (output, err) = p.communicate()

        return output

    def _stream_metrics(self):
        data = self._read_sar_statistics().splitlines()

        header = data[0].strip().split(';')

        for row in data[1:]:
            metrics = row.split(';')
            yield zip(header, metrics)

    def _skip(self, metrics):
        return False

    def deserialize(self):
        stats = {}
        metrics_info_keys = self.metrics_info.keys()

        for metrics in self._stream_metrics():
            if self._skip(metrics):
                continue

            for (metric_name, metric_str) in metrics:
                if metric_name not in metrics_info_keys:
                    continue

                if not stats.get(metric_name):
                    stats[metric_name] = []

                metric = float(metric_str.replace(',', '.'))
                metric = self.metrics_info[metric_name].unit.converter(metric)
                stats[metric_name].append(metric)

        return stats


class CpuSarLogStatistics(SarLogStatistics):

    def __init__(self, stats_src):
        SarLogStatistics.__init__(self, stats_src)

    def _get_sar_system_flag(self):
        return '-u'

    @cached_property
    def metrics_info(self):
        percents = MetricUnit('percents', lambda unit: unit)

        return {
            '%user': MetricInfo('user', percents),
            '%nice': MetricInfo('nice', percents),
            '%system': MetricInfo('system', percents),
            '%iowait': MetricInfo('iowait', percents)
        }


class RamSarLogStatistics(SarLogStatistics):

    def __init__(self, stats_src):
        SarLogStatistics.__init__(self, stats_src)

    def _get_sar_system_flag(self):
        return '-r'

    @cached_property
    def metrics_info(self):
        megabyte = MetricUnit('MB', lambda kb: kb/1024)
        percents = MetricUnit('percents', lambda unit: unit)

        return {
            'kbmemfree': MetricInfo('memfree', megabyte),
            'kbmemused': MetricInfo('memused', megabyte),
            'kbbuffers': MetricInfo('buffers', megabyte),
            'kbcached': MetricInfo('cached', megabyte),
            'kbcommit': MetricInfo('commit', megabyte),
            'kbactive': MetricInfo('active', megabyte),
            'kbinact': MetricInfo('inact', megabyte),
            'kbdirty': MetricInfo('dirty', megabyte),
            '%memused': MetricInfo('memused', percents),
            '%commit': MetricInfo('commit', percents)
        }


class NetworkSarLogStatistics(SarLogStatistics):

    def __init__(self, stats_src, iface=None):
        SarLogStatistics.__init__(self, stats_src)
        self._iface = iface

    def _get_sar_system_flag(self):
        return '-n DEV'

    @cached_property
    def metrics_info(self):
        megabyte = MetricUnit('MB/s', lambda kb: kb/1000)
        percents = MetricUnit('percents', lambda unit: unit)

        return {
            'rxkB/s': MetricInfo('received per sec', megabyte),
            'txkB/s': MetricInfo('transmitted per sec', megabyte),
            '%ifutil': MetricInfo('ifutil', percents)
        }

    def _skip(self, metrics):
        if self._iface:
            return dict(metrics).get('IFACE') != self._iface
        else:
            return False


class QueueSarLogStatistics(SarLogStatistics):

    def __init__(self, stats_src):
        SarLogStatistics.__init__(self, stats_src)

    def _get_sar_system_flag(self):
        return '-q'

    @cached_property
    def metrics_info(self):
        tasks = MetricUnit('number of tasks', lambda num: num)
        return {
            'runq-sz': MetricInfo('queue length', tasks),
            'plist-sz': MetricInfo('task list', tasks),
            'blocked': MetricInfo('blocked', tasks)
        }


class DisksSarLogStatistics(SarLogStatistics):

    def __init__(self, stats_src, disk=None):
        SarLogStatistics.__init__(self, stats_src)
        self._disk = disk

    def _get_sar_system_flag(self):
        return '-d -p' if self._disk else '-b'

    @cached_property
    def metrics_info(self):
        noop = lambda num: num
        block_to_mb = lambda bl: (bl*512)/1000/1000

        transfers_unit = MetricUnit('transfers/s', noop)
        block_to_mb_per_sec_unit = MetricUnit('MB/s', block_to_mb)
        block_to_mb_unit = MetricUnit('MB', block_to_mb)

        for_all = {
            'tps': MetricInfo('transfers num/s', transfers_unit),
            'rtps': MetricInfo('reads num/s', MetricUnit('reads/s', noop)),
            'wtps': MetricInfo('writes num/s', MetricUnit('writes/s', noop)),
            'bread/s': MetricInfo('read/s', block_to_mb_per_sec_unit),
            'bwrtn/s': MetricInfo('write/s', block_to_mb_per_sec_unit)
        }

        for_dev = {
            'tps': MetricInfo('transfers num/s', transfers_unit),
            'rd_sec/s': MetricInfo('read/s', block_to_mb_per_sec_unit),
            'wr_sec/s': MetricInfo('write/s', block_to_mb_per_sec_unit),
            'avgrq-sz': MetricInfo('average req size', block_to_mb_unit),
            'avgqu-sz': MetricInfo('average queue size', MetricUnit('req num', noop)),
            'await': MetricInfo('await', MetricUnit('ms', noop)),
            '%util': MetricInfo('util', MetricUnit('percents', noop))
        }

        return for_dev if self._disk else for_all

    def _skip(self, metrics):
        if self._disk:
            return dict(metrics).get('DEV') != self._disk
        else:
            return False


class StatisticsPlotter(Process):

    def __init__(self, statistics=None, plot_title='Any statistics', export_prefix='', export_dir='.'):
        super(StatisticsPlotter, self).__init__()

        self._statistics = statistics
        self._plot_title = plot_title
        self._export_dir = export_dir
        self._export_prefix = export_prefix

    # def _rearrange_subplots(self, axes):
    #     for i, ax in enumerate(axes):
    #         ax.change_geometry(len(axes), 1, i)
    #
    # def _get_show_hide_fn(self, figure, axes, ax_name_to_index):
    #     visible_axes = list(axes)
    #
    #     def fn(checkbox_label):
    #         ax = axes[ax_name_to_index[checkbox_label]]
    #         ax.set_visible(not ax.get_visible())
    #
    #         if not ax.get_visible():
    #             visible_axes.remove(ax)
    #         else:
    #             visible_axes.append(ax)
    #
    #         self._rearrange_subplots(visible_axes)
    #
    #         figure.canvas.draw()
    #
    #     return fn

    def _do_plot(self):
        stats = self._statistics.deserialize()
        metrics_to_plot = self._statistics.metrics_info
        subplots_count = len(stats)

        if not subplots_count:
            return

        #fig, axarr = plt.subplots(subplots_count)
        #fig.canvas.set_window_title(self._plot_title)

        time = range(len(stats[stats.keys()[0]]))
        #axes_by_names = {}

        metrics_summary_file_name = os.path.join(self._export_dir,
                                                 '%s%s_metrics_summary.txt' % (self._export_prefix, self._plot_title))
        metrics_summary = open(metrics_summary_file_name, 'w')

        for i, key in enumerate(stats.keys()):
            fig = plt.figure()
            fig.canvas.set_window_title(self._plot_title)
            ax = fig.add_subplot(111)

            ax.plot(time, stats[key], label=metrics_to_plot[key].name, lw=1, color=COLORS[i])

            ax.set_xlabel('time (sec)', labelpad=5)
            ax.set_ylabel(metrics_to_plot[key].full_name, labelpad=5)
            ax.yaxis.set_ticks_position('left')
            ax.xaxis.set_ticks_position('bottom')
            #ax.legend()

            #fig.savefig(self._export_prefix + self._plot_title + self._metrics_info[key].name + '.svg', format='svg')
            file_postfix = metrics_to_plot[key].name.replace('/', '_')
            dest_file = '%s[%s]_%s.png' % (self._export_prefix, self._plot_title, file_postfix)
            dest_file_name = os.path.join(self._export_dir, dest_file)
            fig.savefig(dest_file_name, format='png')

            numpy.set_printoptions(precision=1)
            metrics_summary.write('%s_max=%.1f%s' % (file_postfix, numpy.amax(stats[key]), os.linesep))
            metrics_summary.write('%s_5_percentile=%.1f%s' % (file_postfix, numpy.percentile(stats[key], 5), os.linesep))
            metrics_summary.write('%s_50_percentile=%.1f%s' % (file_postfix, numpy.median(stats[key]), os.linesep))
            metrics_summary.write('%s_95_percentile=%.1f%s' % (file_postfix, numpy.percentile(stats[key], 95), os.linesep))
            metrics_summary.write(os.linesep)
            #axes_by_names[key] = i

        metrics_summary.close()
        #rax = plt.axes([0.01, 0.8, 0.1, 0.1])
        #check_btns = CheckButtons(rax, stats.keys(), [True] * subplots_count)
        #check_btns.on_clicked(self._get_show_hide_fn(fig, axarr, axes_by_names))

        #plt.subplots_adjust(left=0.2)
        #plt.show()

    def run(self):
        self._do_plot()


def plot_cpu_stats(params):
    proc = StatisticsPlotter(CpuSarLogStatistics(params.sar_log), 'CPU activity (all cores)', params.export_prefix, params.export_dir)
    proc.start()
    return [proc]


def plot_ram_stats(params):
    proc = StatisticsPlotter(RamSarLogStatistics(params.sar_log), 'Memory activity', params.export_prefix, params.export_dir)
    proc.start()
    return [proc]


def plot_network_stats(params):
    procs = []
    for iface in params.iface:
        proc = StatisticsPlotter(NetworkSarLogStatistics(params.sar_log, iface), 'Network [%s] activity' % iface, params.export_prefix, params.export_dir)
        proc.start()
        procs.append(proc)

    return procs


def plot_queue_stats(params):
    proc = StatisticsPlotter(QueueSarLogStatistics(params.sar_log), 'Queue activity', params.export_prefix, params.export_dir)
    proc.start()
    return [proc]


def plot_disks_stats(params):
    if not params.disks:
        proc = StatisticsPlotter(DisksSarLogStatistics(params.sar_log), 'All disks activity', params.export_prefix, params.export_dir)
        proc.start()
        return [proc]
    else:
        procs = []
        for disk_name in params.disks:
            proc = StatisticsPlotter(DisksSarLogStatistics(params.sar_log, disk_name), 'Disk [%s] activity' % disk_name, params.export_prefix, params.export_dir)
            proc.start()
            procs.append(proc)

        return procs


def plot_stats(params):
    systems = {
        'cpu': plot_cpu_stats,
        'ram': plot_ram_stats,
        'net': plot_network_stats,
        'que': plot_queue_stats,
        'dsk': plot_disks_stats
    }

    procs = []

    for system, plot_fn in systems.items():
        if not params.plots or system in params.plots:
            procs.extend(plot_fn(params))

    for proc in procs:
        proc.join()

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='sr. PLOT SAR', usage=__doc__)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0')
    parser.add_argument('-s', '--sar_log', metavar='FILE', help='a sar log filename')
    parser.add_argument('-p', '--plots', nargs='+', choices=['cpu', 'ram', 'net', 'que', 'dsk'], default=[], help='systems to plot')
    parser.add_argument('-d', '--disks', nargs='+', metavar='DEV', default=[], help='disks names to plot')
    parser.add_argument('-i', '--iface', nargs='+', metavar='IF', default=[], help='network interfaces to plot. Used with "net" plot')
    parser.add_argument("--export-prefix", dest="export_prefix", type=str, default='', help="Exported files prefix")
    parser.add_argument("--export-dir", dest="export_dir", type=str, default='.', help="Destination directory for exported files")

    return_code = plot_stats(parser.parse_args())
    sys.exit(return_code)
