# Describes full workload running cycle.
# Serj Sintsov, 2015
#
from fabric.api import env
from fabric.api import execute
from fabric.api import parallel
from fabric.api import run
from fabric.api import runs_once
from fabric.api import task, roles

import errno
import os
import sys
import yaml


CONFIG_FILE = 'workload_cycle.yaml'

    
def fault(msg):
        print "Error: %s" % msg 
        sys.exit(errno.EIO)

        
def check_arg_not_blank(arg):
    if not arg:
        fault("Expected not blank argument")

        
def read_config(src):
    try:
        f = open(src, 'r')
        return yaml.load(f)
    
    except IOError as e:
        fault( "can not read hosts file '%s': %s" % (src, e.strerror) ) 

        
def init_hosts_settings(cfg):
     env.roledefs['db'] = map(lambda h: h['ip'], cfg.get('hosts'))

     
def init_connection_settings(cfg):
    conn = cfg['connection']
    
    env.use_ssh_config = False
    env.user = conn.get('user')
    env.password = conn.get('password')
    env.key_filename = conn.get('key')

    
def init_env_settings(cfg, workload_name):
    env = cfg['env']
    home_dir = env['home_dir']
    
    env['workload_logs_dir'] = os.path.join(home_dir, env['workload_logs_dir'], workload_name)
    env['system_logs_dir'] = os.path.join(home_dir, env['system_logs_dir'], workload_name)

    
def init(workload_name):
    config = read_config(CONFIG_FILE)

    init_hosts_settings(config)
    init_connection_settings(config)
    init_env_settings(config, workload_name)
    
    return config


def cmd_conj(*commands):
    return ' && '.join(commands)


def get_start_workload_cmd(workload_name):
    return 'sleep 5 && echo %s' % workload_name


@parallel
def execute_workload(workload_name):
    # start sar
    run( get_start_workload_cmd(workload_name) )
    # stop sar


@parallel
def collect_workload_results(workload_name):
    # copy sar logs
    # copy workload logs
    pass


def get_setup_environment_cmd(cfg, workload_name):
    env = cfg['env']
    
    make_home = 'mkdir -p %s' % env['home_dir']
    make_workload_logs = 'mkdir -p %s' % env['workload_logs_dir']
    make_sys_logs = 'mkdir -p %s' % env['system_logs_dir']

    return cmd_conj(make_home, make_workload_logs, make_sys_logs)


@parallel
def setup_environment(cfg, workload_name):
    run( get_setup_environment_cmd(cfg, workload_name) )

    
@parallel
def check_environment(cfg, workload_name):
    pass

        
@task
@runs_once
def test(workload_name):
    '''Starts the whole cycle for specified workload.
       Params: <workload_name>
    '''
    check_arg_not_blank(workload_name)

    cfg = init(workload_name)
    hosts = env.roledefs['db']

    execute( check_environment, cfg, workload_name, hosts=hosts )
    execute( execute_workload, workload_name, hosts=hosts )
    execute( collect_workload_results, workload_name, hosts=hosts ) 


@task
@runs_once
@parallel
def deploy(workload_name):
    '''Deploys specified workload bundle to remote machines.
       Params: <workload_name>
    '''
    check_arg_not_blank(workload_name)

    cfg = init(workload_name)    
    hosts = env.roledefs['db']

    execute( setup_environment, cfg, workload_name, hosts=hosts )    

