"""Describes full workload running cycle.

   Serj Sintsov, 2015
"""
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
from util import make_remote_dirs

from config import BenchmarkConfig


BENCHMARK_CONF_PATH = 'benchmark_conf.yaml' 


def setup_fabric_env(conf):
    conn = conf.connection_parameters

    env.user = conn.get('user')
    env.password = conn.get('password')
    env.key_filename = conn.get('key')

    env.roledefs['clients'] = conf.client_conf.hosts_addresses
    env.roledefs['servers'] = conf.server_conf.hosts_addresses


def execute_shell_scripts(scripts, scripts_names, dest):
    make_remote_dirs(dest)

    for f in scripts:
        put(f, dest)

    with cd(dest):
        for f in scripts_names:
            sudo('sh %s' % f)


@parallel
@roles('clients')
def setup_clients(conf):
    make_remote_dirs(conf.benchmark_home_dir)
    execute_shell_scripts(conf.client_conf.setup_local_scripts,
                          conf.client_conf.setup_scripts_names,
                          conf.client_conf.setup_remote_scripts_dir)
 

@parallel
@roles('servers')
def setup_servers(conf):
    make_remote_dirs(conf.benchmark_home_dir)
    execute_shell_scripts(conf.server_conf.setup_local_scripts,
                          conf.server_conf.setup_scripts_names,
                          conf.server_conf.setup_remote_scripts_dir)


@parallel
@roles('servers')
def setup_servers_db(conf):
    execute_shell_scripts(conf.server_conf.setup_db_local_scripts,
                          conf.server_conf.setup_db_scripts_names,
                          conf.server_conf.setup_db_remote_scripts_dir)


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
    setup_fabric_env(conf)

    execute(setup_servers_db, conf)


@task
@runs_once
def setup_env(config_path=BENCHMARK_CONF_PATH):
    """Setups clients and servers environment (needed packages and setting).
       Params:
           config_path: path to benchmark config if YAML format
    """
    check_arg_not_blank(config_path, 'config_path')
    
    conf = BenchmarkConfig(config_path=config_path)
    setup_fabric_env(conf)

    execute(setup_clients, conf)
    execute(setup_servers, conf)
