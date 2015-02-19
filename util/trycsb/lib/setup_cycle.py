"""Describes full workload running cycle.

   Serj Sintsov, 2015
"""
from fabric import state
from fabric.api import cd
from fabric.api import env
from fabric.api import execute
from fabric.api import parallel
from fabric.api import put
from fabric.api import roles
from fabric.api import runs_once
from fabric.api import task
from fabric.api import sudo

from util import check_arg_not_blank
from util import clear_remote_dirs
from util import make_remote_dirs

from config import BenchmarkConfig


BENCHMARK_CONF_PATH = 'benchmark_conf.yaml' 


def _curr_host():
    return state.env['host']


def _setup_fabric_env(conf):
    conn = conf.connection_parameters

    env.user = conn.get('user')
    env.password = conn.get('password')
    env.key_filename = conn.get('key')


def _config_hosts_or_cli_hosts(conf):
    if not env.hosts:
        return conf.hosts_addresses
    else:
        return env.hosts


def _execute_shell_scripts(sources, scripts_names, dest):
    make_remote_dirs(dest)

    for src in sources:
        put(src, dest)
        
    with cd(dest):
        for f in scripts_names:
            sudo('chmod +x %s' % f)
            sudo('./%s %s' % (f, _curr_host()))


@parallel
def _setup_clients(conf):
    make_remote_dirs(conf.benchmark_remote_home_dir)
    _execute_shell_scripts(conf.client_conf.setup_local_files,
                           conf.client_conf.setup_scripts_names,
                           conf.client_conf.setup_remote_dir)
 

@parallel
def _setup_servers(conf):
    make_remote_dirs(conf.benchmark_remote_home_dir)
    _execute_shell_scripts(conf.server_conf.setup_local_files,
                           conf.server_conf.setup_scripts_names,
                           conf.server_conf.setup_remote_dir)


@parallel
def _setup_servers_db(conf):
    _execute_shell_scripts(conf.server_conf.setup_db_local_files,
                           conf.server_conf.setup_db_scripts_names,
                           conf.server_conf.setup_db_remote_dir)


@task
@runs_once
def setup_db(config_path=BENCHMARK_CONF_PATH, db_profile=None):
    """Setups database.
       Params:
           config_path: path to benchmark config if YAML format
           db_profile : database profile
    """
    check_arg_not_blank(config_path, 'config_path')
    check_arg_not_blank(db_profile, 'db_profile')

    conf = BenchmarkConfig(config_path=config_path, db_profile=db_profile)
    _setup_fabric_env(conf)

    execute(_setup_servers_db, conf, hosts=_config_hosts_or_cli_hosts(conf.server_conf))


@task
@runs_once
def setup_env(config_path=BENCHMARK_CONF_PATH, env_type=None):
    """Setups clients and servers environment (needed packages and setting).
       Params:
           config_path: path to benchmark config if YAML format
           env_type:    type of the environment 'client' or 'server'
    """
    check_arg_not_blank(config_path, 'config_path')
    
    conf = BenchmarkConfig(config_path=config_path)
    _setup_fabric_env(conf)

    if not env_type or env_type == 'client':
        execute(_setup_clients, conf, hosts=_config_hosts_or_cli_hosts(conf.client_conf))

    if not env_type or env_type == 'server':
        execute(_setup_servers, conf, hosts=_config_hosts_or_cli_hosts(conf.server_conf))
