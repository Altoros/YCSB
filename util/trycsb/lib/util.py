"""Util functions.

   Serj Sintsov, 2015
"""
from fabric.api import hide
from fabric.api import local
from fabric.api import run
from fabric.api import sudo

import errno
import sys
import time


def fault(msg):
        print "Error: %s" % msg
        sys.exit(errno.EIO)


def check_arg_not_blank(arg, arg_name):
    if not arg:
        fault("Expected not blank argument '%s'" % arg_name)


def not_empty(value, default=None):
    if not value:
        return default
    return value


def path(*parts):
    return '/'.join(parts)


def get_log_file_name_formatter():
    _START_TIME = time.strftime('%d-%b-%Y_%H-%M-%S')
    return lambda file_name, host: '%s__%s__%s.log' % (file_name, host, _START_TIME)


def install_pckg(pckg):
    sudo('apt-get install -y %s' % pckg)


def restart_daemon(name):
    sudo('service %s restart' % name)


def pid(cmd):
    get_pid_cmd = "ps -eo pid,command | grep \"%s\"  | grep -v grep | awk '{print $1}'"
    get_pid_cmd = get_pid_cmd % cmd

    return run(get_pid_cmd)


def bg_sudo(src_cmd, out='/dev/null'):
    """Executes command which creates only one process.
       Returns pid of forked process.
    """
    bg_cmd = 'nohup %s >%s 2>&1 &' % (src_cmd, out)

    sudo(bg_cmd, pty=False)
    return pid(src_cmd)


def sudo_kill_11(*pids):
    for pid in pids:
        if pid:
            sudo('kill -11 %s' % pid)


def cmd_conj(commands):
    return ' && '.join(commands)


def replace_in_sys_file(target_file, pattern, result):
    cmd = 'sed -i.bak \'s/%s/%s/\' %s' % (pattern, result, target_file)
    sudo(cmd)


def _make_dirs(is_local=False, *dirs):
    mkdir = lambda (dir_name): 'mkdir -p %s' % dir_name
    commands = map(mkdir, map(list, dirs)[0])

    if is_local:
        local(cmd_conj(commands))
    else:
        run(cmd_conj(commands))


def make_local_dirs(*dirs):
    _make_dirs(True, dirs)


def make_remote_dirs(*dirs):
    _make_dirs(False, dirs)


def _clear_dirs(is_local=False, *dirs):
    clear_dir = lambda (dir_name): 'rm %s' % path(dir_name, '*')
    commands  = map(clear_dir, filter(bool, map(list, dirs)[0]))

    if is_local:
        local(cmd_conj(commands))
    else:
        run(cmd_conj(commands))


def clear_remote_dirs(*dirs):
    _clear_dirs(False, dirs)


def tar(src):
    out = '%s.tar.gz' % src
    run('tar -czf %s %s' % (out, src))
    return out
