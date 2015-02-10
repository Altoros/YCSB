"""Variable scripts. Used to start/stop/kill services and process,
   update configs from test to test
"""
from fabric.api import env
from fabric.api import execute
from fabric.api import parallel
from fabric.api import roles
from fabric.api import runs_once
from fabric.api import sudo
from fabric.api import task

from lib.util import check_arg_not_blank

from lib.config import BenchmarkConfig


BENCHMARK_CONF_PATH = 'benchmark_conf.yaml' 


def setup_fabric_env(conf):
    conn = conf.connection_parameters

    env.user = conn.get('user')
    env.password = conn.get('password')
    env.key_filename = conn.get('key')

    env.roledefs['clients'] = conf.client_conf.hosts_addresses
    env.roledefs['servers'] = conf.server_conf.hosts_addresses


@parallel
@roles('servers')
def kill_application():
    sudo('service mysql stop')
    sudo('service apache2 stop')
    sudo('service bind9 stop')


@task
@runs_once
def prepare_servers(benchmark_conf_path=BENCHMARK_CONF_PATH):
    check_arg_not_blank(benchmark_conf_path, 'benchmark_conf_path')

    conf = BenchmarkConfig(benchmark_conf_path)
    setup_fabric_env(conf)

    execute(kill_application, conf)
