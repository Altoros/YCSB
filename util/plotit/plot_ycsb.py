#!/usr/bin/env python

""" Plots values you gave from YCSB logging.
    As the result you'll get graphs of latency function,
    throughput function and operations function.
"""
import argparse
import os
import re
import sys
import numpy

from cached_property import cached_property

from common import *

from multiprocessing import Process
from matplotlib import pyplot as plt


class YCSBLogParser:

    INSERT = 'INSERT'
    UPDATE = 'UPDATE'
    READ = 'READ'
    THROUGHPUT = 'THROUGHPUT'
    OPERATIONS = 'OPERATIONS'
    TIME = 'TIME'

    def __init__(self, time_step=1):
        self._time_step = time_step

    @cached_property
    def metrics_info(self):
        us_str_to_ms = MetricUnit('ms', lambda us: float(us)/1000)
        str_to_float = lambda v: float(v)

        return {
            YCSBLogParser.INSERT: MetricInfo('insert latency', us_str_to_ms),
            YCSBLogParser.UPDATE: MetricInfo('update latency', us_str_to_ms),
            YCSBLogParser.READ:   MetricInfo('read latency', us_str_to_ms),
            YCSBLogParser.THROUGHPUT: MetricInfo('throughput', MetricUnit('tps', str_to_float)),
            YCSBLogParser.OPERATIONS: MetricInfo('operations', MetricUnit('count', str_to_float)),
            YCSBLogParser.TIME: MetricInfo('time', MetricUnit('sec'))
        }

    def _stream_metrics_tokens(self, log_file_name):
        splitter = re.compile('[ =\\[\\]]')

        with open(log_file_name) as f:
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

    def deserialize(self, log_file_name):
        stats = {
            YCSBLogParser.THROUGHPUT: [],
            YCSBLogParser.OPERATIONS: [],
            YCSBLogParser.INSERT: [],
            YCSBLogParser.UPDATE: [],
            YCSBLogParser.READ: []
        }

        for metrics_tokens in self._stream_metrics_tokens(log_file_name):
            if len(metrics_tokens) <= 6:
                stats[YCSBLogParser.OPERATIONS].append(0)
                stats[YCSBLogParser.THROUGHPUT].append(0)
                stats[YCSBLogParser.INSERT].append(0)
                stats[YCSBLogParser.UPDATE].append(0)
                stats[YCSBLogParser.READ].append(0)
            else:
                stats[YCSBLogParser.OPERATIONS].append(self.metrics_info[YCSBLogParser.OPERATIONS].unit.converter(metrics_tokens[3]))
                stats[YCSBLogParser.THROUGHPUT].append(self.metrics_info[YCSBLogParser.THROUGHPUT].unit.converter(metrics_tokens[5]))

                for k, v in self._extract_latencies(metrics_tokens):
                    stats[k].append(self.metrics_info[k].unit.converter(v))

        stats[YCSBLogParser.TIME] = list(xrange(0,
                                                self._time_step*len(stats[YCSBLogParser.OPERATIONS]),
                                                self._time_step))

        return stats


class StatisticsPlotter(Process):

    def __init__(self, metrics_set=None, labels=None, metrics_info=None, plot_title='Any statistics', export_prefix=''):
        super(StatisticsPlotter, self).__init__()

        self._metrics_set = metrics_set
        self._labels = labels
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
        if not self._metrics_set:
            return

        #metric_filter = lambda k: k != YCSBLogParser.TIME and len(self._metrics_set[k]) == len(self._metrics_set[YCSBLogParser.TIME])
        #metric_names = filter(metric_filter, self._metrics_set.keys())
        #subplots_count = len(metric_names)

        #if not subplots_count:
        #    return

        #fig, axarr = plt.subplots(nrows=self._get_subplots_in_col(subplots_count),
        #                          ncols=self._get_subplots_in_row(subplots_count))

        #axes_by_names = {}

        for metric_name, metric_info in self._metrics_info.items():
            if metric_name == YCSBLogParser.TIME:
                continue

            fig = plt.figure()
            fig.canvas.set_window_title(self._plot_title)
            ax = fig.add_subplot(111)
            ax.set_xlabel(self._metrics_info[YCSBLogParser.TIME].full_name, labelpad=5)
            ax.set_ylabel(metric_info.full_name, labelpad=5)
            ax.yaxis.set_ticks_position('left')
            ax.xaxis.set_ticks_position('bottom')

            metrics_summary_file_name = '%sycsb_metrics_summary_%s.txt' % (self._export_prefix, metric_name)
            metrics_summary_file_name = metrics_summary_file_name.replace(' ', '_')
            metrics_summary = open(metrics_summary_file_name, 'w')

            to_save = False
            i = 0
            for metrics in self._metrics_set:
                if metrics.get(metric_name) and (len(metrics[YCSBLogParser.TIME]) == len(metrics[metric_name])):
                    marker3 = len(metrics[metric_name])
                    marker1 = marker3/2
                    marker2 = marker1 + marker1/2
                    markers = numpy.array([marker1, marker2, marker3])

                    ax.plot(metrics[YCSBLogParser.TIME], metrics[metric_name],
                            label=self._labels[i],
                            lw=1,
                            #marker=MARKERS[i],
                            #markevery=markers,
                            color=COLORS[i])
                    i += 1
                    to_save = True

                    metrics_summary.write('%s_max=%.3f%s' % (i, numpy.amax(metrics[metric_name]), os.linesep))
                    metrics_summary.write('%s_5_percentile=%.3f%s' % (i, numpy.percentile(metrics[metric_name], 5), os.linesep))
                    metrics_summary.write('%s_50_percentile=%.3f%s' % (i, numpy.median(metrics[metric_name]), os.linesep))
                    metrics_summary.write('%s_95_percentile=%.3f%s' % (i, numpy.percentile(metrics[metric_name], 95), os.linesep))
                    metrics_summary.write('%s_99_percentile=%.3f%s' % (i, numpy.percentile(metrics[metric_name], 99), os.linesep))
                    metrics_summary.write(os.linesep)

            if to_save:
                ax.legend(numpoints=1)
                #fig.savefig(self._export_prefix + self._metrics_info[key].name + '.svg', format='svg')
                fig.savefig(self._export_prefix + metric_name + '.png', format='png')
                #axes_by_names[key] = i

            metrics_summary.close()
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

    ycsb_parser = YCSBLogParser(params.time_step)

    metrics_set = []
    for log in params.ycsb_logs:
        metrics_set.append(ycsb_parser.deserialize(log))

    plotter = StatisticsPlotter(metrics_set, params.plot_labels, ycsb_parser.metrics_info, 'YCSB statistics', params.export_prefix)
    plotter.start()
    plotter.join()


def validate_params(params):
    errs = []

    if not params.ycsb_logs:
        errs.append('YCSB log file has to be specified')
        return errs

    for log in params.ycsb_logs:
        if not os.path.isfile(log):
            errs.append('Can not read YCSB log file "%s"' % log)

    if len(params.plot_labels) != len(params.ycsb_logs):
        errs.append('Specify labels for all YCSB log files')

    return errs


if __name__ == "__main__":
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument("--ycsb-logs", dest="ycsb_logs", nargs='+', type=str, default=[], help="YCSB log files")
    parser.add_argument("--plot-labels", dest="plot_labels", nargs='+', type=str, default=[], help="Plots lables to display in legend")
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
