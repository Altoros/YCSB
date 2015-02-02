# Describes full workload running cycle.
# Serj Sintsov, 2015
#
from fabric import state
from fabric.api import cd
from fabric.api import env
from fabric.api import execute
from fabric.api import hide
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


BENCHMARK_CONF_PATH = 'benchmark_conf.yaml' 
WORKLOAD_DB_CONF_PATH = 'db_conf.yaml'
START_TIME  = time.strftime('%d-%b-%Y_%H-%M-%S')


def fault(msg):
        print "Error: %s" % msg 
        sys.exit(errno.EIO)


def check_arg_not_blank(arg):
    if not arg:
        fault("Expected not blank argument")


def path(*parts):
    return '/'.join(parts)


def get_log_file_name(file_name, host):
    return '%s__%s__%s.log' % (file_name, host, START_TIME)


def pid(cmd):
    get_pid_cmd = "ps -eo pid,command | grep \"%s\"  | grep -v grep | awk '{print $1}'"
    get_pid_cmd = get_pid_cmd % cmd

    with hide('running', 'stdout', 'stderr'):
        return run(get_pid_cmd)

    
def bg_sudo(src_cmd, out='/dev/null'):
    bg_cmd = 'nohup %s >%s 2>&1 &' % (src_cmd, out)        
    sudo(bg_cmd, pty=False)
    return pid(src_cmd)

    
def cmd_conj(*commands):
    return ' && '.join(commands)


def get_replace_cmd(pattern, result, target_file):
    return 'sed -i.bak \'s/%s/%s/\' %s' % (pattern, result, target_file)


class BenchmarkConfig():
    def __init__(self, config_path, workload_name):
        self._conf = self._init(config_path)
        self._workload_name = workload_name

    def _init(self, config_path):
        conf = self._parse_config(config_path)

        self._init_connection_settings(conf)
        
        return conf
        
    def _parse_config(self, src):
        try:
            f = open(src, 'r')
            return yaml.load(f)

        except IOError as e:
            fault( "can not read hosts file '%s': %s" % (src, e.strerror) ) 

    def _init_connection_settings(self, conf):
        conn = conf['connection']

        env.user     = conn.get('user')
        env.password = conn.get('password')
        env.key_filename = conn.get('key')

    def clients_addresses(self):
        return map(lambda h: h['addr'], self._conf.get('clients'))

    def workload_name(self):
        return self._workload_name
    
    def workload_logs_dir(self):
        conf = self._conf    
        return path( conf['home_dir'], conf['logs_dir'], self._workload_name )

    def workload_logs_dir(self):
        return self._conf['home_dir']
        
    def options(self):
        return self._self

    
def get_start_system_stats_cmd(conf, host):
    log_file = get_log_file_name( '%s-stats' % conf.workload_name(), host )
    log_path = path( conf.workload_logs_dir(), log_file )
     
    return 'sar -o %s 1 15' % log_path


def get_stop_system_stats_cmd(pid): 
    return 'kill -11 %s' % pid


def get_start_workload_cmd(conf, host):
    log_file = get_log_file_name(conf.workload_name(), host)
    log_path = path( conf.workload_logs_dir(), log_file )
    
    return 'java -jar ycsb.jar %s >%s 2>&1' % (params, log_path)

        
def get_setup_environment_cmd(conf):
    mkdir = 'mkdir -p %s'

    make_home = mkdir % conf.workload_home_dir()
    make_logs = mkdir % conf.workload_logs_dir()

    return cmd_conj( make_home, make_logs )


@parallel
def execute_workload(conf):
    host = state.env['host']
    
    stats_pid = bg_sudo( get_start_system_stats_cmd(conf, host) )
    #run( get_start_workload_cmd(conf, host) )
    sudo( get_stop_system_stats_cmd(stats_pid) )


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
    for src in conf.options().get('bundles'): 
        put(src, conf.workload_home_dir())

        
@task
@runs_once
def test(benchmark_conf_path=BENCHMARK_CONF_PATH, workload_name=None,
         db_profile=None):
    '''Starts the whole cycle for specified benchmark.
    '''
    check_arg_not_blank(workload_name)

    conf  = BenchmarkConfig(benchmark_conf_path, workload_name)
    hosts = conf.clients_addresses()

    execute( execute_workload, conf, hosts=hosts )
    execute( collect_workload_results, conf, hosts=hosts ) 


@task
@runs_once
def setup(benchmark_conf_path=BENCHMARK_CONF_PATH, workload_name=None):
    '''Setups environment for benchmarks and deploys specified
       workload bundle to remote machines.
    '''
    check_arg_not_blank(workload_name)
    check_arg_not_blank(benchmark_conf_path)
    
    conf  = BenchmarkConfig(benchmark_conf_path, workload_name)    
    hosts = conf.clients_addresses()

    execute( setup_environment, conf, hosts=hosts )    
    execute( deploy_workload, conf, hosts=hosts )
 
