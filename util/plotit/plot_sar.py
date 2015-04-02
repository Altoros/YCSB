"""

"""
import argparse
import sys
import subprocess

from multiprocessing import Process
from matplotlib import pyplot as plt
from matplotlib.widgets import CheckButtons


COLORS = ['#008000',  # green
          '#000000',  # black
          '#0033FF',  # blue
          '#9933CC',  # purple
          '#FF3366',  # red
          '#FF6600',  # orange
          '#8B4513',  # saddle brown
          '#008080',  # teal
          '#EE82EE',  # violet
          '#6A5ACD']  # slate blue


class MetricUnit(object):

    def __init__(self, name, converter):
        self._name = name
        self._converter = converter

    @property
    def name(self):
        return self._name

    @property
    def converter(self):
        return self._converter


class MetricInfo(object):

    def __init__(self, name, unit):
        self._name = name
        self._unit = unit

    @property
    def name(self):
        return self._name

    @property
    def unit(self):
        return self._unit


class SarLogStatistics(object):

    def __init__(self, stats_src):
        self._stats_src = stats_src

    def get_metrics_to_plot(self):
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
        metrics_to_plot = self.get_metrics_to_plot().keys()

        for metrics in self._stream_metrics():
            if self._skip(metrics):
                continue

            for (metric_name, metric_str) in metrics:
                if metric_name not in metrics_to_plot:
                    continue

                if not stats.get(metric_name):
                    stats[metric_name] = []

                metric = float(metric_str.replace(',', '.'))
                metric = self.get_metrics_to_plot()[metric_name].unit.converter(metric)
                stats[metric_name].append(metric)

        return stats


class CpuSarLogStatistics(SarLogStatistics):

    def __init__(self, stats_src):
        SarLogStatistics.__init__(self, stats_src)

    def _get_sar_system_flag(self):
        return '-u'

    def get_metrics_to_plot(self):
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

    def get_metrics_to_plot(self):
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

    def get_metrics_to_plot(self):
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

    def get_metrics_to_plot(self):
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

    def get_metrics_to_plot(self):
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

    def __init__(self, statistics=None, plot_title='Any statistics'):
        super(StatisticsPlotter, self).__init__()

        self._statistics = statistics
        self._plot_title = plot_title

    def _rearrange_subplots(self, axes):
        for i, ax in enumerate(axes):
            ax.change_geometry(len(axes), 1, i)

    def _get_show_hide_fn(self, figure, axes, ax_name_to_index):
        visible_axes = list(axes)

        def fn(checkbox_label):
            ax = axes[ax_name_to_index[checkbox_label]]
            ax.set_visible(not ax.get_visible())

            if not ax.get_visible():
                visible_axes.remove(ax)
            else:
                visible_axes.append(ax)

            self._rearrange_subplots(visible_axes)

            figure.canvas.draw()

        return fn

    def _do_plot(self):
        stats = self._statistics.deserialize()
        metrics_to_plot = self._statistics.get_metrics_to_plot()
        subplots_count = len(stats)

        fig, axarr = plt.subplots(subplots_count)
        fig.canvas.set_window_title(self._plot_title)

        time = range(len(stats[stats.keys()[0]]))
        axes_by_names = {}

        for i, key in enumerate(stats.keys()):
            axarr[i].plot(time, stats[key], label=metrics_to_plot[key].name, lw=1, color=COLORS[i])
            axarr[i].set_xlabel('time (sec)')
            axarr[i].set_ylabel(metrics_to_plot[key].unit.name)
            axarr[i].legend()
            axes_by_names[key] = i


        rax = plt.axes([0.01, 0.8, 0.1, 0.1])
        check_btns = CheckButtons(rax, stats.keys(), [True] * subplots_count)
        check_btns.on_clicked(self._get_show_hide_fn(fig, axarr, axes_by_names))

        plt.subplots_adjust(left=0.2)
        plt.show()

    def run(self):
        self._do_plot()


def plot_cpu_stats(params):
    proc = StatisticsPlotter(CpuSarLogStatistics(params.sar_log), 'CPU activity (all cores)')
    proc.start()
    return [proc]


def plot_ram_stats(params):
    proc = StatisticsPlotter(RamSarLogStatistics(params.sar_log), 'Memory activity')
    proc.start()
    return [proc]


def plot_network_stats(params):
    procs = []
    for iface in params.iface:
        proc = StatisticsPlotter(NetworkSarLogStatistics(params.sar_log, iface), 'Network [%s] activity' % iface)
        proc.start()
        procs.append(proc)

    return procs


def plot_queue_stats(params):
    proc = StatisticsPlotter(QueueSarLogStatistics(params.sar_log), 'Queue activity')
    proc.start()
    return [proc]


def plot_disks_stats(params):
    if not params.disks:
        proc = StatisticsPlotter(DisksSarLogStatistics(params.sar_log), 'All disks activity')
        proc.start()
        return [proc]
    else:
        procs = []
        for disk_name in params.disks:
            proc = StatisticsPlotter(DisksSarLogStatistics(params.sar_log, disk_name), 'Disk [%s] activity' % disk_name)
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
        if system in params.plots:
            procs.extend(plot_fn(params))

    for proc in procs:
        proc.join()

    return 0


class ListAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, **kwargs):
        super(ListAction, self).__init__(option_strings, dest, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        val_list = []
        if values:
            val_list = values.split(',')

        setattr(namespace, self.dest, val_list)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='sr. PLOT SAR', usage=__doc__)
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    parser.add_argument('--sar_log', type=str, help='SAR log filename')
    parser.add_argument('--plots', action=ListAction, help='Systems (separated by comma) to plot. Possible values: cpu, ram, dsk, net, que')
    parser.add_argument('--disks', action=ListAction, help='Disks devices names (separated by comma) to plot')
    parser.add_argument('--iface', action=ListAction, help='Network interfaces (separated by comma) to plot. Used with net plot')

    return_code = plot_stats(parser.parse_args())
    sys.exit(return_code)
