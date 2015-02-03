# Describes full workload running cycle.
# Serj Sintsov, 2015
#
from fabric import state
from fabric.api import cd
from fabric.api import env
from fabric.api import execute
from fabric.api import get
from fabric.api import hide
from fabric.api import local
from fabric.api import parallel
from fabric.api import put
from fabric.api import run
from fabric.api import runs_once
from fabric.api import sudo
from fabric.api import settings
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


def install_pckg(pckg):
    sudo('apt-get install -y %s' % pckg)


def restart_daemon(name):
    sudo('service %s restart' % name)

    
def pid(cmd):
    get_pid_cmd = "ps -eo pid,command | grep \"%s\"  | grep -v grep | awk '{print $1}'"
    get_pid_cmd = get_pid_cmd % cmd

    with hide('running', 'stdout', 'stderr'):
        return run(get_pid_cmd)

    
def bg_sudo(src_cmd, out='/dev/null'):
    '''Executes command which creates only one process.
       Returns pid of forked process.
    '''
    bg_cmd = 'nohup %s >%s 2>&1 &' % (src_cmd, out)
            
    sudo(bg_cmd, pty=False)
    return pid(src_cmd)


def sudo_kill_11(*pids):
    for pid in pids: 
        sudo('kill -11 %s' % pid)

    
def cmd_conj(*commands):
    return ' && '.join(commands)


def replace_in_sys_file(target_file, pattern, result):
    cmd = 'sed -i.bak \'s/%s/%s/\' %s' % (pattern, result, target_file)
    sudo(cmd)


class BenchmarkConfig():
    def __init__(self, config_path, workload_name, workload_db_conf_path=None,
                 db_profile=None):
        self._workload_name = workload_name
        self._db_profile = db_profile
        
        self._conf = self._init_benchmark_settings(config_path)       

        if db_profile:
            self._init_db_settings(workload_db_conf_path)
            
    def _init_benchmark_settings(self, config_path):
        conf = self._parse_config(config_path)

        self._validate_benchmark_settings(conf)
        self._init_connection_settings(conf)
        
        return conf
        
    def _validate_benchmark_settings(self, conf):
        workloads_opts = conf.get('workloads')    
        if not workloads_opts:
            fault("No options for workloads")
            
        if not workloads_opts.get(self._workload_name):
            fault("No options for workload '%s'" % self._workload_name)
    
    def _init_connection_settings(self, conf):
        conn = conf['connection']

        env.user     = conn.get('user')
        env.password = conn.get('password')
        env.key_filename = conn.get('key')

    def _init_db_settings(self, config_path):
        db_conf = self._parse_config(config_path)

        self._validate_db_settings(db_conf)

        workload_conf = self._conf['workloads'][self._workload_name]
        workload_conf['db'] = db_conf.get(self._db_profile)
        
        return config_path

    def _validate_db_settings(self, db_conf):            
        if not db_conf.get(self._db_profile):
            fault("No options for db profile '%s'" % self._db_profile)

    def _parse_config(self, src):
        try:
            f = open(src, 'r')
            return yaml.load(f)

        except IOError as e:
            fault( "can not read hosts file '%s': %s" % (src, e.strerror) ) 

    def _not_empty(self, value, default=None):
        if not value:
            return default
        return value
    
    def clients_addresses(self):
        return map(lambda h: h['addr'], self._conf.get('clients'))

    def benchmark_home_dir(self):
        return self._not_empty( self._conf['remote_home_dir'], '.' )

    def benchmark_local_home_dir(self):
        return self._not_empty( self._conf['local_home_dir'], '.' )
    
    def workload_name(self):
        return self._workload_name
    
    def db_profile(self):
        return self._db_profile

    def workload_local_logs_dir(self):
        local_logs_dir = self._not_empty( self._conf['local_logs_dir'], '.' )

        return path( self.benchmark_local_home_dir(), local_logs_dir,
                     self.db_profile() )

    def workload_options(self):
        return self._conf['workloads'][self._workload_name]

    def workload_logs_dir(self):
        remote_logs_dir = self._not_empty( self._conf['remote_logs_dir'], '.' )

        return path( self.benchmark_home_dir(), remote_logs_dir,
                     self.workload_name() )

    def options(self):
        return self._conf


def get_stats_log_path(conf, host):
    log_file = get_log_file_name( '%s-stats' % conf.workload_name(), host )
    return path( conf.workload_logs_dir(), log_file )

            
def start_system_stats(conf, host):
    log_path = get_stats_log_path(conf, host)
    cmd = 'sar -o %s 1 15' % log_path
    
    return bg_sudo(cmd)


def get_ycsb_options(conf):
    ycsb_opts = conf.workload_options().get('ycsb')
    db_opts   = conf.workload_options().get('db')
    
    property_to_str = lambda k, v: '%s=%s' % (k, v)
    dict_to_list  = lambda dic, fn: [fn(k, v) for (k, v) in dic.iteritems()]

    options = []
    options += ycsb_opts.get('options')
    options += dict_to_list( ycsb_opts.get('properties'), property_to_str )
    options += dict_to_list( db_opts.get('ycsb'), property_to_str ) 
    options += dict_to_list( db_opts.get('specific'), property_to_str ) 

    return ' '.join(options)
    

def get_workload_log_path(conf, host):
    log_file = get_log_file_name(conf.workload_name(), host)
    return path( conf.workload_logs_dir(), log_file )    

    
def execute_workload(conf, host):
    options  = get_ycsb_options(conf)
    log_path = get_workload_log_path(conf, host)
       
    cmd = 'java -jar ycsb.jar %s >%s 2>&1' % (options, log_path)
    with cd(conf.benchmark_home_dir()):
        run( cmd, warn_only=True )

       
@parallel
def execute_benchmark(conf):
    host = state.env['host']
    
    stats_pids = start_system_stats(conf, host)
    execute_workload(conf, host)
    sudo_kill_11(stats_pids)


def create_benchmark_local_dirs(conf):
    mkdir = 'mkdir -p %s'

    make_home = mkdir % conf.benchmark_local_home_dir()
    make_logs = mkdir % conf.workload_local_logs_dir()

    local( cmd_conj( make_home, make_logs ) )

    
@parallel
def collect_benchmark_results(conf):
    host = state.env['host']

    create_benchmark_local_dirs(conf)
    get( get_workload_log_path(conf, host), conf.workload_local_logs_dir() )
    get( get_stats_log_path(conf, host), conf.workload_local_logs_dir() )


def setup_java():
    install_pckg('openjdk-7-jre-headless')

    
def setup_sar():
    install_pckg('sysstat')
    replace_in_sys_file('/etc/default/sysstat', 'ENABLED="false"',
                        'ENABLED="true"')
    restart_daemon('sysstat')


def create_benchmark_dirs(conf):
    mkdir = 'mkdir -p %s'

    make_home = mkdir % conf.benchmark_home_dir()
    make_logs = mkdir % conf.workload_logs_dir()

    run( cmd_conj( make_home, make_logs ) )

        
@parallel
def setup_benchmark_environment(conf):
    create_benchmark_dirs(conf)
    setup_java()
    setup_sar()

    
@parallel
def deploy_benchmark_bundle(conf):
    for src in conf.options().get('bundles'): 
        put(src, conf.benchmark_home_dir())


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

    execute( setup_benchmark_environment, conf, hosts=hosts )    
    execute( deploy_benchmark_bundle, conf, hosts=hosts )


@task
@runs_once
def deploy(benchmark_conf_path=BENCHMARK_CONF_PATH, workload_name=None):
    '''Deploys benchmark bundle for specified workload.
    '''
    check_arg_not_blank(workload_name)
    check_arg_not_blank(benchmark_conf_path)
    
    conf  = BenchmarkConfig(benchmark_conf_path, workload_name)    

    execute( deploy_benchmark_bundle, conf, hosts=conf.clients_addresses() )

        
@task
@runs_once
def test(benchmark_conf_path=BENCHMARK_CONF_PATH, workload_name=None,
         workload_db_conf_path=WORKLOAD_DB_CONF_PATH, db_profile=None):
    '''Starts the whole cycle for specified benchmark.
    '''
    check_arg_not_blank(benchmark_conf_path)
    check_arg_not_blank(workload_name)
    check_arg_not_blank(db_profile)

    conf  = BenchmarkConfig(benchmark_conf_path, workload_name,
                            workload_db_conf_path, db_profile)
    hosts = conf.clients_addresses()

    execute( execute_benchmark, conf, hosts=hosts )
    execute( collect_benchmark_results, conf, hosts=hosts ) 

