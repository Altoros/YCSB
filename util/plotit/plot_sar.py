"""

"""
import argparse
import sys
import subprocess

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


class SarLogSerializer(object):

    def __init__(self, stats_src):
        self._stats_src = stats_src

    def _get_metric_names(self):
        raise NotImplementedError('Please Implement this method')

    def _get_sar_system_flag(self):
        raise NotImplementedError('Please Implement this method')

    def _read_sar_binary_data(self):
        cmd = 'sadf -d %s -- %s' % (self._stats_src, self._get_sar_system_flag())

        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
        (output, err) = p.communicate()

        return output

    def deserialize(self):
        data = self._read_sar_binary_data().splitlines()

        stats = {}
        metric_names = data[0].strip().split(';')

        for metric_name in metric_names:
            if metric_name in self._get_metric_names():
                stats[metric_name] = []

        for metrics_str in data[1:]:
            metrics = metrics_str.split(';')

            for (metric_name, metric) in zip(metric_names, metrics):
                if metric_name in self._get_metric_names():
                    metric = metric.replace(',', '.')
                    stats[metric_name].append(metric)

        return stats


class CpuSarLogSerializer(SarLogSerializer):

    def __init__(self, stats_src):
        SarLogSerializer.__init__(self, stats_src)

    def _get_sar_system_flag(self):
        return '-u'

    def _get_metric_names(self):
        return ['%user', '%nice', '%system', '%iowait']


class RamSarLogSerializer(SarLogSerializer):

    def __init__(self, stats_src):
        SarLogSerializer.__init__(self, stats_src)

    def _get_sar_system_flag(self):
        return '-r'

    def _get_metric_names(self):
        return ['kbmemfree', 'kbmemused', 'kbbuffers', 'kbcached', 'kbcommit',
                'kbactive', 'kbinact', 'kbdirty', '%memused', '%commit']

    def deserialize(self):
        stats = super(RamSarLogSerializer, self).deserialize()

        ram_stats = {
            'absolute': {},
            'percents': {}
        }

        for (k, v) in stats.items():
            if k.startswith('%'):
                ram_stats['percents'][k] = v
            else:
                ram_stats['absolute'][k] = v

        return ram_stats


class NetworkSarLogSerializer(SarLogSerializer):

    def __init__(self, stats_src):
        SarLogSerializer.__init__(self, stats_src)

    def _get_sar_system_flag(self):
        return '-n DEV'

    def _get_metric_names(self):
        return ['rxkB/s', 'txkB/s', '%ifutil']


class QueueSarLogSerializer(SarLogSerializer):

    def __init__(self, stats_src):
        SarLogSerializer.__init__(self, stats_src)

    def _get_sar_system_flag(self):
        return '-q'

    def _get_metric_names(self):
        return ['runq-sz', 'plist-sz', 'blocked']


class DisksSarLogSerializer(SarLogSerializer):

    def __init__(self, stats_src, all_disks=False):
        SarLogSerializer.__init__(self, stats_src)
        self._all_disks = all_disks

    def _get_sar_system_flag(self):
        return '-b' if self._all_disks else '-d -p'

    def _get_metric_names(self):
        for_all = ['tps', 'rtps', 'wtps', 'bread/s', 'bwrtn/s']
        for_dev = ['tps', 'rd_sec/s', 'wr_sec/s', 'avgrq-sz', 'avgqu-sz', 'await', 'svctm', '%util']

        return for_all if self._all_disks else for_dev

    def _disks_deserialize(self):
        data = self._read_sar_binary_data().splitlines()

        stats = {}
        metric_names = data[0].strip().split(';')
        dev_col_index = metric_names.index('DEV')

        for metrics_str in data[1:]:
            metrics = metrics_str.split(';')
            dev_name = metrics[dev_col_index]

            if not stats.get(dev_name):
                stats[dev_name] = {}

            for (metric_name, metric) in zip(metric_names, metrics):
                if metric_name in self._get_metric_names():
                    if not stats[dev_name].get(metric_name):
                        stats[dev_name][metric_name] = []

                    metric = metric.replace(',', '.')
                    stats[dev_name][metric_name].append(metric)

        return stats

    def deserialize(self):
        if self._all_disks:
            return super(DisksSarLogSerializer, self).deserialize()
        else:
            return self._disks_deserialize()


def plot_any_system_stats(stats, plot_title):
    stats_names = list(stats.keys())

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
    serializer = CpuSarLogSerializer(params.sar_log)
    return [fork_plot(plot_any_system_stats, (serializer.deserialize(), 'CPU activity (all cores)'))]


def plot_ram_stats(params):
    serializer = RamSarLogSerializer(params.sar_log)
    stats = serializer.deserialize()

    proc1 = fork_plot(plot_any_system_stats, (stats['absolute'], 'Memory activity (kilobytes)'))
    proc2 = fork_plot(plot_any_system_stats, (stats['percents'], 'Memory activity (percents)'))

    return [proc1, proc2]


def plot_network_stats(params):
    serializer = NetworkSarLogSerializer(params.sar_log)
    return [fork_plot(plot_any_system_stats, (serializer.deserialize(), 'Network activity'))]


def plot_queue_stats(params):
    serializer = QueueSarLogSerializer(params.sar_log)
    return [fork_plot(plot_any_system_stats, (serializer.deserialize(), 'Queue activity'))]


def plot_disks_stats(params):
    disks = []
    if params.disks:
        disks = params.disks.split(',')

    serializer = DisksSarLogSerializer(params.sar_log, not disks)
    stats = serializer.deserialize()

    procs = []
    if not disks:
        procs.append(fork_plot(plot_any_system_stats, (stats, 'All disks activity')))
    else:
        for disk_name in disks:
            procs.append(fork_plot(plot_any_system_stats, (stats[disk_name], 'Disk [%s] activity' % disk_name)))

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

