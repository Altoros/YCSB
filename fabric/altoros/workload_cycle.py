# Describes full workload running cycle.
# Serj Sintsov, 2015
#
from fabric import state
from fabric.api import cd
from fabric.api import env
from fabric.api import execute
from fabric.api import parallel
from fabric.api import put
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
START_TIME  = time.strftime('%d-%b-%Y_%H-%M-%S')


def fault(msg):
        print "Error: %s" % msg 
        sys.exit(errno.EIO)


def check_arg_not_blank(arg):
    if not arg:
        fault("Expected not blank argument")


def path(*parts):
    return '/'.join(parts)


def parse_config(src):
    try:
        f = open(src, 'r')
        return yaml.load(f)

    except IOError as e:
        fault( "can not read hosts file '%s': %s" % (src, e.strerror) ) 


def init_hosts_settings(conf):
    conf['addresses'] = map(lambda h: h['addr'], conf.get('hosts'))


def init_connection_settings(conf):
    conn = conf['connection']

    env.user     = conn.get('user')
    env.password = conn.get('password')
    env.key_filename = conn.get('key')


def init_workload_settings(conf, workload_name):
    workload = conf['workload']
    workload['name'] = workload_name
    workload['logs_dir'] = path( workload['home_dir'], workload['logs_dir'], workload_name )


def init(workload_name):
    conf = parse_config(CONFIG_FILE)

    init_hosts_settings(conf)
    init_connection_settings(conf)
    init_workload_settings(conf, workload_name)

    return conf

    
def get_log_file_name(file_name, host):
    return '%s__%s__%s.log' % (file_name, host, START_TIME)


def cmd_conj(*commands):
    return ' && '.join(commands)


def get_replace_cmd(pattern, result, target_file):
    return 'sed -i.bak \'s/%s/%s/\' %s' % (pattern, result, target_file)

    
def get_start_system_stats_cmd(conf, host):
    workload      = conf['workload']
    workload_name = workload['name']
    log_file = get_log_file_name( '%s-stats' % workload_name, host )
    log_path = path( workload['logs_dir'], log_file )
     
    return 'sar -o %s 1 5 >/dev/null 2>&1' % log_path


def get_stop_system_stats_cmd(pid): 
    return 'kill -11 %s' % pid


def get_start_workload_cmd(conf, host):
    workload      = conf['workload']
    workload_name = workload['name']
    log_file = get_log_file_name(workload_name, host)
    log_path = path( workload['logs_dir'], log_file )
    
    return 'nohup sleep 5 && echo %s > %s &' % (workload_name, log_path)

        
def get_setup_environment_cmd(conf):
    mkdir = 'mkdir -p %s'

    workload  = conf['workload']
    make_home = mkdir % workload['home_dir']
    make_logs = mkdir % workload['logs_dir']

    return cmd_conj( make_home, make_logs )


@parallel
def execute_workload(conf):
    host = state.env['host']
    stats_pid = sudo( get_start_system_stats_cmd(conf, host) )
    #run( get_start_workload_cmd(workload_name, state.env['host']) )
    #sudo( get_stop_system_stats_cmd(pid) )


@parallel
def collect_workload_results(conf):
    # copy sar logs
    # copy workload logs
    pass


def setup_sar():
    sudo('apt-get install sysstat')
    sudo( get_replace_cmd('ENABLED="false"', 'ENABLED="true"', '/etc/default/sysstat') )
    sudo('service sysstat restart')

        
@parallel
def setup_environment(conf):
    run( get_setup_environment_cmd(conf) )
    setup_sar()

    
@parallel
def deploy_workload(conf):
    workload = conf['workload']

    with cd(workload['home_dir']):
        for src in workload.get('bundles'): 
            put(src)

        
@task
@runs_once
def test(workload_name):
    '''Starts the whole cycle for specified workload.
       Params: <workload_name>
    '''
    check_arg_not_blank(workload_name)

    conf  = init(workload_name)
    hosts = conf['addresses']

    execute( execute_workload, conf, hosts=hosts )
    execute( collect_workload_results, conf, hosts=hosts ) 


@task
@runs_once
def setup(workload_name):
    '''Setups environment and deploys specified workload bundle to remote machines.
       Params: <workload_name>
    '''
    check_arg_not_blank(workload_name)

    conf  = init(workload_name)    
    hosts = conf['addresses']

    execute( setup_environment, conf, hosts=hosts )    
    execute( deploy_workload, conf, hosts=hosts )
 
