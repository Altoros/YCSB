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


def fork_plot(plot_fn, fn_args):
    proc = Process(None, target=plot_fn, args=fn_args)
    proc.start()
    return proc


def join_proc(proc):
    if proc:
        proc.join()


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


class SarLogSerializer(object):

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

    def deserialize(self):
        data = self._read_sar_statistics().splitlines()

        stats = {}
        all_metric_names = data[0].strip().split(';')
        metrics_to_plot = self.get_metrics_to_plot().keys()

        for metric_name in all_metric_names:
            if metric_name in metrics_to_plot:
                stats[metric_name] = []

        for metrics_str in data[1:]:
            metrics = metrics_str.split(';')

            for (metric_name, metric_str) in zip(all_metric_names, metrics):
                if metric_name in metrics_to_plot:
                    metric = float(metric_str.replace(',', '.'))
                    metric = self.get_metrics_to_plot()[metric_name].unit.converter(metric)
                    stats[metric_name].append(metric)

        return stats


class CpuSarLogSerializer(SarLogSerializer):

    def __init__(self, stats_src):
        SarLogSerializer.__init__(self, stats_src)

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


class RamSarLogSerializer(SarLogSerializer):

    def __init__(self, stats_src):
        SarLogSerializer.__init__(self, stats_src)

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


class NetworkSarLogSerializer(SarLogSerializer):

    def __init__(self, stats_src):
        SarLogSerializer.__init__(self, stats_src)

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


class QueueSarLogSerializer(SarLogSerializer):

    def __init__(self, stats_src):
        SarLogSerializer.__init__(self, stats_src)

    def _get_sar_system_flag(self):
        return '-q'

    def get_metrics_to_plot(self):
        tasks = MetricUnit('number of tasks', lambda num: num)
        return {
            'runq-sz': MetricInfo('queue length', tasks),
            'plist-sz': MetricInfo('task list', tasks),
            'blocked': MetricInfo('blocked', tasks)
        }


class DisksSarLogSerializer(SarLogSerializer):

    def __init__(self, stats_src, all_disks=False):
        SarLogSerializer.__init__(self, stats_src)
        self._all_disks = all_disks

    def _get_sar_system_flag(self):
        return '-b' if self._all_disks else '-d -p'

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

        return for_all if self._all_disks else for_dev

    def _disks_deserialize(self):
        data = self._read_sar_statistics().splitlines()

        stats = {}
        metric_names = data[0].strip().split(';')
        dev_col_index = metric_names.index('DEV')

        for metrics_str in data[1:]:
            metrics = metrics_str.split(';')
            dev_name = metrics[dev_col_index]

            if not stats.get(dev_name):
                stats[dev_name] = {}

            for (metric_name, metric_str) in zip(metric_names, metrics):
                if metric_name in self.get_metrics_to_plot():
                    if not stats[dev_name].get(metric_name):
                        stats[dev_name][metric_name] = []

                    metric = float(metric_str.replace(',', '.'))
                    metric = self.get_metrics_to_plot()[metric_name].unit.converter(metric)

                    stats[dev_name][metric_name].append(metric)

        return stats

    def deserialize(self):
        if self._all_disks:
            return super(DisksSarLogSerializer, self).deserialize()
        else:
            return self._disks_deserialize()


def plot_any_system_stats(stats, metrics_to_plot, plot_title):
    def rearrange_subplots(axes):
        for i, ax in enumerate(axes):
            ax.change_geometry(len(axes), 1, i)

    def get_show_hide_fn(figure, axes, ax_name_to_index):
        visible_axes = list(axes)

        def fn(checkbox_label):
            ax = axes[ax_name_to_index[checkbox_label]]
            ax.set_visible(not ax.get_visible())

            if not ax.get_visible():
                visible_axes.remove(ax)
            else:
                visible_axes.append(ax)

            rearrange_subplots(visible_axes)

            figure.canvas.draw()

        return fn

    def do_plot():
        subplots_count = len(stats)

        fig, axarr = plt.subplots(subplots_count)
        fig.canvas.set_window_title(plot_title)

        time = range( len(stats[stats.keys()[0]]) )
        axes_by_names = {}

        for i, key in enumerate(stats.keys()):
            axarr[i].plot(time, stats[key], label=metrics_to_plot[key].name, lw=1, color=COLORS[i])
            axarr[i].set_xlabel('time (sec)')
            axarr[i].set_ylabel(metrics_to_plot[key].unit.name)
            axarr[i].legend()
            axes_by_names[key] = i


        rax = plt.axes([0.01, 0.8, 0.1, 0.1])
        check_btns = CheckButtons(rax, stats.keys(), [True] * subplots_count)
        check_btns.on_clicked(get_show_hide_fn(fig, axarr, axes_by_names))

        plt.subplots_adjust(left=0.2)
        plt.show()

    do_plot()


def plot_cpu_stats(params):
    serializer = CpuSarLogSerializer(params.sar_log)
    fork_args = (serializer.deserialize(), serializer.get_metrics_to_plot(), 'CPU activity (all cores)')
    return [fork_plot(plot_any_system_stats, fork_args)]


def plot_ram_stats(params):
    serializer = RamSarLogSerializer(params.sar_log)
    fork_args = (serializer.deserialize(), serializer.get_metrics_to_plot(), 'Memory activity')
    return [fork_plot(plot_any_system_stats, fork_args)]


def plot_network_stats(params):
    serializer = NetworkSarLogSerializer(params.sar_log)
    fork_args = (serializer.deserialize(), serializer.get_metrics_to_plot(), 'Network activity')
    return [fork_plot(plot_any_system_stats, fork_args)]


def plot_queue_stats(params):
    serializer = QueueSarLogSerializer(params.sar_log)
    fork_args = (serializer.deserialize(), serializer.get_metrics_to_plot(), 'Queue activity')
    return [fork_plot(plot_any_system_stats, fork_args)]


def plot_disks_stats(params):
    disks = []
    if params.disks:
        disks = params.disks.split(',')

    serializer = DisksSarLogSerializer(params.sar_log, not disks)
    stats = serializer.deserialize()

    procs = []
    if not disks:
        fork_args = (stats, serializer.get_metrics_to_plot(), 'All disks activity')
        procs.append(fork_plot(plot_any_system_stats, fork_args))
    else:
        for disk_name in disks:
            fork_args = (stats[disk_name], serializer.get_metrics_to_plot(), 'Disk [%s] activity' % disk_name)
            procs.append(fork_plot(plot_any_system_stats, fork_args))

    return procs


def plot_stats(params):
    systems = {
        'cpu': plot_cpu_stats,
        'ram': plot_ram_stats,
        'net': plot_network_stats,
        'que': plot_queue_stats,
        'dsk': plot_disks_stats
    }

    systems_to_plot = []
    if params.plots:
       systems_to_plot = params.plots.split(',')

    procs = []

    for system, plot_fn in systems.items():
        if not systems_to_plot or system in systems_to_plot:
            procs.extend(plot_fn(params))

    for proc in procs:
        join_proc(proc)

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument('--sar_log', type=str, required=True, help='SAR log filename')
    parser.add_argument('--disks', type=str, help='Disks devices names (separated by comma) to plot')
    parser.add_argument('--plots', type=str, help='Systems (separated by comma) to plot. Possible values: cpu, ram, dsk, net, que')
    args = parser.parse_args()

    return_code = plot_stats(args)
    sys.exit(return_code)
