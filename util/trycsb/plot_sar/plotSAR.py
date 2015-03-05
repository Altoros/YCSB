__author__ = 'vladimir.starostenkov'

import argparse
import os
from pylab import plot, show, legend, figure


def main():
    parser = argparse.ArgumentParser(usage=__doc__)
    parser.add_argument("--sar_log", type=str, help="SAR log filename")
    args = parser.parse_args()

    if not os.path.isfile(args.sar_log):
        print "File not found, check your --sar_log"
        return

    fig = figure()
    # CPU usage:
    fig.add_subplot(311)
    #plot_subsystem(args.sar_log, " ", ["%user", "%nice", "%system", "%iowait", "%steal", "%idle"])
    plot_subsystem(args.sar_log, " ", ["%user", "%nice", "%system", "%iowait", "%steal"])
    legend()

    # RAM usage:
    #fig.add_subplot(312)
    #plot_subsystem(args.sar_log, "-q", ["runq-sz", "plist-sz", "ldavg-1", "ldavg-5", "ldavg-15", "blocked"])
    #plot_subsystem(args.sar_log, "-q", ["runq-sz", "ldavg-1", "ldavg-5", "ldavg-15", "blocked"])
    #legend()

    # RAM usage:
    fig.add_subplot(312)
    plot_subsystem(args.sar_log, "-r", ["kbmemfree", "kbmemused", "%memused", "kbbuffers", "kbcached", "kbcommit", "%commit", "kbactive", "kbinact", "kbdirty"])
    legend()

    # Disk usage:
    fig.add_subplot(313)
    plot_subsystem(args.sar_log, "-b", ["tps", "rtps", "wtps", "bread/s", "bwrtn/s"])
    legend()

    show()

#def plot_cpu(filename, columns_to_plot):
#    os.system("sadf -d {} > CPU.log".format(filename))
#    cpu = get_columns("CPU.log", columns_to_plot)
#
#    t = range(len(cpu[cpu.keys()[0]]))
#    for key in cpu.keys():
#        plot(t, cpu[key], label=key)

def plot_subsystem(filename, susbystem_sar_arg, columns_to_plot):
    os.system("sadf -d {} -- {} > temp.log".format(filename, susbystem_sar_arg))
    data = get_columns("temp.log", columns_to_plot)

    t = range(len(data[data.keys()[0]]))
    for key in data.keys():
        plot(t, data[key], label=key)

def get_columns(filename, column_names):
    columns = {}
    with open(filename) as log:
        data = log.readlines()
        names = data[0].strip().split(";")
        for name in names:
            columns[name] = []
        for line in data[1:]:
            line_points = line.split(';')
            [columns[x].append(y) for (x, y) in zip(names, line_points)]

    return {key: columns[key] for key in column_names}

if __name__ == "__main__":
    main()

