#!/usr/bin/env python

""" Plots values you gave from YCSB logging.
    As the result you'll get graphs of latency function,
    throughput function and operations function.
"""
import argparse
import os
import re
import sys

from common import *

from multiprocessing import Process
from matplotlib import pyplot as plt


class YCSBLogParser(object):

    INSERT = 'INSERT'
    UPDATE = 'UPDATE'
    READ = 'READ'
    THROUGHPUT = 'THROUGHPUT'
    OPERATIONS = 'OPERATIONS'
    TIME = 'TIME'

    def __init__(self, ycsb_log, time_step=1):
        self._ycsb_log = ycsb_log
        self._time_step = time_step

    def get_metrics_info(self):
        us_str_to_ms = MetricUnit('ms', lambda us: float(us)/1000)
        str_to_float = lambda v: float(v)

        return {
            YCSBLogParser.INSERT: MetricInfo('insert latensy', us_str_to_ms),
            YCSBLogParser.UPDATE: MetricInfo('update latensy', us_str_to_ms),
            YCSBLogParser.READ:   MetricInfo('read latensy', us_str_to_ms),
            YCSBLogParser.THROUGHPUT: MetricInfo('throughput', MetricUnit('tps', str_to_float)),
            YCSBLogParser.OPERATIONS: MetricInfo('operations', MetricUnit('count', str_to_float)),
            YCSBLogParser.TIME: MetricInfo('time', MetricUnit('sec'))
        }

    def _stream_metrics_tokens(self):
        splitter = re.compile('[ =\\[\\]]')

        with open(self._ycsb_log) as f:
            for line in f.readlines():
                if line.find(' sec: ') == -1:
                    continue

                tokens = splitter.split(line)
                yield tokens

    def _extract_latencies(self, metrics_tokens):
        i = 6
        while i < len(metrics_tokens):
            if metrics_tokens[i] in [YCSBLogParser.INSERT, YCSBLogParser.UPDATE, YCSBLogParser.READ]:
                yield (metrics_tokens[i], metrics_tokens[i+2])
                i += 3
            else:
                i += 1

    def deserialize(self):
        stats = {
            YCSBLogParser.THROUGHPUT: [],
            YCSBLogParser.OPERATIONS: [],
            YCSBLogParser.INSERT: [],
            YCSBLogParser.UPDATE: [],
            YCSBLogParser.READ: []
        }

        metrics_info = self.get_metrics_info()

        for metrics_tokens in self._stream_metrics_tokens():
            if len(metrics_tokens) <= 6:
                stats[YCSBLogParser.OPERATIONS].append(0)
                stats[YCSBLogParser.THROUGHPUT].append(0)
                stats[YCSBLogParser.INSERT].append(0)
                stats[YCSBLogParser.UPDATE].append(0)
                stats[YCSBLogParser.READ].append(0)
            else:
                stats[YCSBLogParser.OPERATIONS].append(metrics_info[YCSBLogParser.OPERATIONS].unit.converter(metrics_tokens[3]))
                stats[YCSBLogParser.THROUGHPUT].append(metrics_info[YCSBLogParser.THROUGHPUT].unit.converter(metrics_tokens[5]))

                for k, v in self._extract_latencies(metrics_tokens):
                    stats[k].append(metrics_info[k].unit.converter(v))

        stats[YCSBLogParser.TIME] = list(xrange(0,
                                                self._time_step*len(stats[YCSBLogParser.OPERATIONS]),
                                                self._time_step))

        return stats


class StatisticsPlotter(Process):

    def __init__(self, stats={}, metrics_info={}, plot_title='Any statistics', export_prefix=''):
        super(StatisticsPlotter, self).__init__()

        self._stats = stats
        self._metrics_info = metrics_info
        self._plot_title = plot_title
        self._export_prefix = export_prefix

    # def _rearrange_subplots(self, axes):
    #     for i, ax in enumerate(axes):
    #         ax.change_geometry(self._get_subplots_in_col(len(axes)),
    #                            self._get_subplots_in_row(len(axes)), i)
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
    #
    # def _get_subplots_in_col(self, total_subplots):
    #     return 1 if total_subplots <= 3 else total_subplots/3
    #
    # def _get_subplots_in_row(self, total_subplots):
    #     return 3 if total_subplots >= 3 else total_subplots

    def _do_plot(self):
        if YCSBLogParser.TIME not in self._stats:
            return

        metric_filter = lambda k: k != YCSBLogParser.TIME and len(self._stats[k]) == len(self._stats[YCSBLogParser.TIME])
        metric_names = filter(metric_filter, self._stats.keys())
        subplots_count = len(metric_names)

        if not subplots_count:
            return

        #fig, axarr = plt.subplots(nrows=self._get_subplots_in_col(subplots_count),
        #                          ncols=self._get_subplots_in_row(subplots_count))

        axes_by_names = {}

        for i, key in enumerate(metric_names):
            fig = plt.figure()
            fig.canvas.set_window_title(self._plot_title)
            ax = fig.add_subplot(111)
            ax.plot(self._stats[YCSBLogParser.TIME], self._stats[key],
                      label=self._metrics_info[key].name,
                      lw=1,
                      color=COLORS[i])

            ax.set_xlabel(self._metrics_info[YCSBLogParser.TIME].name, labelpad=10)
            ax.set_ylabel(self._metrics_info[key].unit.name, labelpad=10)
            ax.set_title('', y=1.05)
            ax.yaxis.set_ticks_position('left')
            ax.xaxis.set_ticks_position('bottom')
            #ax.legend()
            fig.savefig(self._export_prefix + self._metrics_info[key].name + '.svg', format='svg')
            fig.savefig(self._export_prefix + self._metrics_info[key].name + '.png', format='png')
            #axes_by_names[key] = i

        #rax = plt.axes([0.01, 0.8, 0.1, 0.1])
        #check_btns = CheckButtons(rax, metric_names, [True] * subplots_count)
        #check_btns.on_clicked(self._get_show_hide_fn(fig, axarr, axes_by_names))

        #plt.subplots_adjust(left=0.2)
        #plt.show()

    def run(self):
        self._do_plot()


#class YCSBPlotGUI(QWidget):
#    def __init__(self, parent=None):
#        super(YCSBPlotGUI, self).__init__(parent)



def plot(params):
    #app = QApplication(sys.argv)
    #gui = YCSBPlotGUI()
    #gui.show()
    #return app.exec_()

    ycsb_parser = YCSBLogParser(params.ycsb_log, params.time_step)
    stats  = ycsb_parser.deserialize()

    plotter = StatisticsPlotter(stats, ycsb_parser.get_metrics_info(), 'YCSB statistics', params.export_prefix)
    plotter.start()
    plotter.join()


def validate_params(params):
    errs = []

    if not params.ycsb_log:
        errs.append('YCSB log file has to be specified')
    elif not os.path.isfile(params.ycsb_log):
        errs.append('Can not read YCSB log file')

    return errs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument("--ycsb-log", dest="ycsb_log", type=str, help="YCSB log file with status outputs")
    parser.add_argument("--time-step", dest="time_step", type=int, default=2, help="Time step")
    parser.add_argument("--export-prefix", dest="export_prefix", type=str, default='', help="Exported files prefix")
    params = parser.parse_args()

    errors = [] #validate_params(args)
    if len(errors) > 0:
        for err in errors:
            print err

        sys.exit(1)

    plot(params)
    sys.exit(0)
