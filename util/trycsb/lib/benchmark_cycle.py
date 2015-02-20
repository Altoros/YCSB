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
from util import get_log_file_name_formatter
from util import make_local_dirs
from util import make_remote_dirs
from util import path
from util import sudo_kill_11
from util import tar

from config import BenchmarkConfig


_BENCHMARK_CONF_PATH = 'benchmark_conf.yaml'


log_file_name_formatter = get_log_file_name_formatter()


def _curr_host():
    return state.env['host']


def _setup_fabric_env(conf):
    conn = conf.connection_parameters

    env.user = conn.get('user')
    env.password = conn.get('password')
    env.key_filename = conn.get('key')

    env.roledefs['clients'] = conf.client_conf.hosts_addresses
    env.roledefs['servers'] = conf.server_conf.hosts_addresses


def _get_stats_log_path(conf, host):
    log_file = log_file_name_formatter('%s-stats' % conf.workload_name, host)
    return path(conf.benchmark_remote_logs_dir, log_file)


@parallel
@roles('servers')
def _start_server_stats(conf):
    log_path = _get_stats_log_path(conf, _curr_host())
    cmd = 'sar -o %s 1 %s' % (log_path, 2*60*60)  # monitor stats limit is 2 hours

    return bg_sudo(cmd)


@parallel
@roles('servers')
def _stop_server_stats(host_to_pids):
    sudo_kill_11(host_to_pids[_curr_host()])


def _get_ycsb_options(conf):
    wl_params = conf.client_conf.workload_parameters
    db_params = conf.client_conf.db_parameters

    value_to_str = lambda v: ','.join(v) if isinstance(v, list) else v
    prop_to_str  = lambda k, v: '-p %s=%s' % (k, value_to_str(v))
    dict_to_list = lambda dic, fn: [fn(k, v) for (k, v) in dic.iteritems()]

    options = []
    options += wl_params.get('options')
    options += dict_to_list(wl_params.get('properties'), prop_to_str)
    options += dict_to_list(db_params, prop_to_str)

    return ' '.join(options)
    

def _get_workload_log_path(conf, host):
    log_file = log_file_name_formatter(conf.workload_name, host)
    return path(conf.benchmark_remote_logs_dir, log_file)


@parallel
@roles('clients')
def _execute_workload(conf):
    ycsbexe  = conf.client_conf.ycsb_executable_name
    options  = _get_ycsb_options(conf)
    log_path = _get_workload_log_path(conf, _curr_host())

    cmd = 'java -jar %s %s >%s 2>&1' % (ycsbexe, options, log_path)

    with cd(conf.benchmark_remote_home_dir):
        run(cmd, warn_only=True)


@parallel
@roles('servers')
def _collect_benchmark_server_results(conf):
    target = tar(_get_stats_log_path(conf, _curr_host()))
    get(target, conf.benchmark_local_logs_dir)


@parallel
@roles('clients')
def _collect_benchmark_client_results(conf):
    target = tar(_get_workload_log_path(conf, _curr_host()))
    get(target, conf.benchmark_local_logs_dir)


@parallel
@roles('clients', 'servers')
def _setup_workload_environment(conf):
    make_remote_dirs(conf.benchmark_remote_logs_dir)


def _test_cycle(conf):
    execute(_setup_workload_environment, conf)
    start_server_stats_result = execute(_start_server_stats, conf)
    execute(_execute_workload, conf)
    execute(_stop_server_stats, start_server_stats_result)

    make_local_dirs(conf.benchmark_local_logs_dir)
    execute(_collect_benchmark_server_results, conf)
    execute(_collect_benchmark_client_results, conf)


@parallel
@roles('clients')
def _deploy_benchmark(conf):
    make_remote_dirs(conf.benchmark_remote_home_dir)

    for src in conf.client_conf.uploads:
        put(src, conf.benchmark_remote_home_dir)


def _deploy_cycle(conf):
    execute(_deploy_benchmark, conf)


@task
@runs_once
def benchmark_deploy(config_path=_BENCHMARK_CONF_PATH):
    """Deploys benchmark bundle for specified workload.
       Params:
           config_path: path to benchmark config if YAML format
    """
    check_arg_not_blank(config_path, 'config_path')

    conf = BenchmarkConfig(config_path=config_path)
    _setup_fabric_env(conf)

    _deploy_cycle(conf)


@task
@runs_once
def benchmark_run(config_path=_BENCHMARK_CONF_PATH, workload_name=None,
                  db_profile=None):
    """Starts the whole cycle for specified benchmark.
       Params:
           config_path  : path to benchmark config if YAML format
           workload_name: name of workload to run
           db_profile   : name of DB profile to use in workload
    """
    check_arg_not_blank(config_path, 'config_path')
    check_arg_not_blank(workload_name, 'workload_name')
    check_arg_not_blank(db_profile, 'db_profile')

    conf = BenchmarkConfig(config_path=config_path, workload_name=workload_name,
                           db_profile=db_profile)
    _setup_fabric_env(conf)
    
    _test_cycle(conf)
