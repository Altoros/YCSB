# Describes full workload running cycle.
# Serj Sintsov, 2015
#
from fabric.api import env
from fabric.api import execute
from fabric.api import parallel
from fabric.api import run
from fabric.api import runs_once
from fabric.api import sudo
from fabric.api import task

import errno
import os
import sys
import time
import yaml


CONFIG_FILE = 'workload_cycle.yaml'
START_TIME  = time.strftime('%Y-%d-%b_%H-%M-%S')


def fault(msg):
        print "Error: %s" % msg 
        sys.exit(errno.EIO)


def check_arg_not_blank(arg):
    if not arg:
        fault("Expected not blank argument")


def parse_config(src):
    try:
        f = open(src, 'r')
        return yaml.load(f)

    except IOError as e:
        fault( "can not read hosts file '%s': %s" % (src, e.strerror) ) 


def init_hosts_settings(conf):
    conf['hosts']['addresses'] = map(lambda h: h['ip'], conf.get('hosts'))


def init_connection_settings(conf):
    conn = conf['connection']

    env.user     = conn.get('user')
    env.password = conn.get('password')
    env.key_filename = conn.get('key')


def init_env_settings(conf, workload_name):
    env      = conf['env']
    home_dir = env['home_dir']

    env['workload_logs_dir'] = os.path.join( home_dir, env['workload_logs_dir'], workload_name )
    env['system_logs_dir']   = os.path.join( home_dir, env['system_logs_dir'], workload_name )


def init(workload_name):
    conf = parse_config(CONFIG_FILE)

    init_hosts_settings(conf)
    init_connection_settings(conf)
    init_env_settings(conf, workload_name)

    return conf


def get_log_file_name(file_name, host):
    return '%s__%s__%s.log' % (file_name, host, START_TIME)


def cmd_conj(*commands):
    return ' && '.join(commands)


def get_start_system_stats_cmd(workload_name, host):
    stats_log = get_log_file_name( '%s-stats' % workload_name, host ) 
    return 'sleep 15 && echo stats_%s > %s' % (workload_name, stats_log)


def get_stop_system_stats_cmd(pid): 
    return 'kill -11 %s' % pid


def get_start_workload_cmd(workload_name, host):
    workload_log = get_log_file_name(workload_name, host)
    return 'sleep 5 && echo %s > %s' % (workload_name, workload_log)


def get_setup_environment_cmd(conf, workload_name):
    env   = conf['env']
    mkdir = 'mkdir -p %s'

    make_home          = mkdir % env['home_dir']
    make_workload_logs = mkdir % env['workload_logs_dir']
    make_sys_logs      = mkdir % env['system_logs_dir']

    return cmd_conj(make_home, make_workload_logs, make_sys_logs)


@parallel
def execute_workload(workload_name):
    stats_pid = sudo( get_start_system_stats_cmd(workload_name) )
    run( get_start_workload_cmd(workload_name) )
    sudo( get_stop_system_stats_cmd(pid) )


@parallel
def collect_workload_results(workload_name):
    # copy sar logs
    # copy workload logs
    pass


@parallel
def setup_environment(conf, workload_name):
    run( get_setup_environment_cmd(conf, workload_name) )


@parallel
def check_environment(conf, workload_name):
    pass


@task
@runs_once
def test(workload_name):
    '''Starts the whole cycle for specified workload.
       Params: <workload_name>
    '''
    check_arg_not_blank(workload_name)

    conf  = init(workload_name)
    hosts = conf['hosts']['addresses']

    execute( check_environment, conf, workload_name, hosts=hosts )
    execute( execute_workload, workload_name, hosts=hosts )
    execute( collect_workload_results, workload_name, hosts=hosts ) 


@task
@runs_once
def deploy(workload_name):
    '''Deploys specified workload bundle to remote machines.
       Params: <workload_name>
    '''
    check_arg_not_blank(workload_name)

    conf  = init(workload_name)    
    hosts = conf['hosts']['addresses']

    execute( setup_environment, conf, workload_name, hosts=hosts )    

