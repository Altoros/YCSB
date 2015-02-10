"""Describes full workload running cycle.
   Serj Sintsov, 2015
"""
from fabric import state
from fabric.api import cd
from fabric.api import env
from fabric.api import execute
from fabric.api import get
from fabric.api import parallel
from fabric.api import put
from fabric.api import roles
from fabric.api import run
from fabric.api import runs_once
from fabric.api import task

from util import bg_sudo
from util import check_arg_not_blank
from util import get_log_file_name
from util import make_local_dirs
from util import make_remote_dirs
from util import path
from util import sudo_kill_11

from config import BenchmarkConfig

import time


BENCHMARK_CONF_PATH = 'benchmark_conf.yaml' 
START_TIME = time.strftime('%d-%b-%Y_%H-%M-%S')


def curr_host():
    return state.env['host']


def setup_fabric_env(conf):
    conn = conf.connection_parameters

    env.user = conn.get('user')
    env.password = conn.get('password')
    env.key_filename = conn.get('key')

    env.roledefs['clients'] = conf.client_conf.hosts_addresses
    env.roledefs['servers'] = conf.server_conf.hosts_addresses


def get_stats_log_path(conf, host):
    log_file = get_log_file_name( '%s-stats' % conf.workload_name, START_TIME, host )
    return path(conf.workload_logs_dir, log_file)


@parallel
@roles('servers')
def start_server_stats(conf):
    log_path = get_stats_log_path(conf, curr_host())
    cmd = 'sar -o %s 1 %s' % (log_path, 2*60*60)  # monitor stats limit is 2 hours

    return bg_sudo(cmd)


@parallel
@roles('servers')
def stop_server_stats(host_to_pids):
    sudo_kill_11(host_to_pids[curr_host()])


def get_ycsb_options(conf):
    ycsb_params = conf.client_conf.workload_parameters.get('ycsb')
    db_params   = conf.client_conf.db_profile_parameters.get('ycsb')

    value_to_str    = lambda v: ','.join(v) if isinstance(v, list) else v
    property_to_str = lambda k, v: '-p %s=%s' % (k, value_to_str(v))
    dict_to_list    = lambda dic, fn: [fn(k, v) for (k, v) in dic.iteritems()]

    options = []
    options += ycsb_params.get('options')
    options += dict_to_list(ycsb_params.get('properties'), property_to_str)
    options += dict_to_list(db_params, property_to_str)

    return ' '.join(options)
    

def get_workload_log_path(conf, host):
    log_file = get_log_file_name(conf.workload_name, START_TIME, host)
    return path(conf.workload_logs_dir, log_file)


@parallel
@roles('clients')
def execute_workload(conf):
    ycsbexe  = conf.client_conf.ycsb_executable_name
    options  = get_ycsb_options(conf)
    log_path = get_workload_log_path(conf, curr_host())

    cmd = 'java -jar %s %s >%s 2>&1' % (ycsbexe, options, log_path)

    with cd(conf.benchmark_home_dir):
        run(cmd, warn_only=True)


@parallel
@roles('servers')
def collect_benchmark_server_results(conf):
    get( get_stats_log_path(conf, curr_host()), conf.workload_local_logs_dir )


@parallel
@roles('clients')
def collect_benchmark_client_results(conf):
    get( get_workload_log_path(conf, curr_host()), conf.workload_local_logs_dir )


@parallel
@roles('clients', 'servers')
def setup_workload_environment(conf):
    make_remote_dirs(conf.workload_logs_dir)


def test_cycle(conf):
    execute(setup_workload_environment, conf)
    start_server_stats_result = execute(start_server_stats, conf)
    execute(execute_workload, conf)
    execute(stop_server_stats, start_server_stats_result)

    make_local_dirs(conf.workload_local_logs_dir)

    execute(collect_benchmark_server_results, conf)
    execute(collect_benchmark_client_results, conf)


@parallel
@roles('clients')
def deploy_benchmark(conf):
    make_remote_dirs(conf.benchmark_home_dir)

    for src in conf.client_conf.bundles:
        put(src, conf.benchmark_home_dir)


def deploy_cycle(conf):
    execute(deploy_benchmark, conf)


@task
@runs_once
def deploy_benchmark(benchmark_conf_path=BENCHMARK_CONF_PATH):
    """Deploys benchmark bundle for specified workload.
       Params:
           benchmark_conf_path: path to benchmark config if YAML format
           workload_name      : name of workload to run
    """
    check_arg_not_blank(benchmark_conf_path, 'benchmark_conf_path')

    conf = BenchmarkConfig(benchmark_conf_path)
    setup_fabric_env(conf)

    deploy_cycle(conf)


@task
@runs_once
def run_benchmark(benchmark_conf_path=BENCHMARK_CONF_PATH, workload_name=None,
                  db_profile=None):
    """Starts the whole cycle for specified benchmark.
       Params:
           benchmark_conf_path: path to benchmark config if YAML format
           workload_name      : name of workload to run
           db_profile         : name of DB profile to use in workload
    """
    check_arg_not_blank(benchmark_conf_path, 'benchmark_conf_path')
    check_arg_not_blank(workload_name, 'workload_name')
    check_arg_not_blank(db_profile, 'db_profile')

    conf = BenchmarkConfig(benchmark_conf_path, workload_name, db_profile)
    setup_fabric_env(conf)
    
    test_cycle(conf)
