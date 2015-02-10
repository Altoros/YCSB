# Describes full workload running cycle.
# Serj Sintsov, 2015
#
from fabric.api import env
from fabric.api import execute
from fabric.api import parallel
from fabric.api import roles
from fabric.api import runs_once
from fabric.api import sudo
from fabric.api import task
from lib.util import make_remote_dirs

from util import check_arg_not_blank
from util import install_pckg
from util import replace_in_sys_file
from util import restart_daemon

from config import BenchmarkConfig


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
def setup_cassandra():
    pass


@parallel
@roles('clients', 'servers')
def setup_java():
    install_pckg('software-properties-common')
    sudo('apt-add-repository -y ppa:webupd8team/java')
    sudo('apt-get update')
    install_pckg('oracle-java7-installer')
    install_pckg('oracle-java7-set-default')


@parallel
@roles('clients', 'servers')
def setup_sar():
    install_pckg('sysstat')
    replace_in_sys_file('/etc/default/sysstat', 'ENABLED="false"', 'ENABLED="true"')
    restart_daemon('sysstat')


@parallel
@roles('clients', 'servers')
def create_benchmark_dirs(conf):
    make_remote_dirs(conf.benchmark_home_dir)


def setup_env_cycle(conf):
    execute(create_benchmark_dirs, conf)
    execute(setup_sar)
    execute(setup_java)


@task
@runs_once
def env_setup(benchmark_conf_path=BENCHMARK_CONF_PATH):
    """Setups clients and servers environment (needed packages and setting).
       Params:
           benchmark_conf_path: path to benchmark config if YAML format
    """
    check_arg_not_blank(benchmark_conf_path, 'benchmark_conf_path')
    
    conf = BenchmarkConfig(benchmark_conf_path)
    setup_fabric_env(conf)

    setup_env_cycle(conf)


@task
@runs_once
def db_setup(benchmark_conf_path=BENCHMARK_CONF_PATH, db_profile=None):
    """Setups database.
       Params:
           benchmark_conf_path: path to benchmark config if YAML format
           db_profile: database profile
    """
    check_arg_not_blank(benchmark_conf_path, 'benchmark_conf_path')
    check_arg_not_blank(db_profile, 'db_profile')

    conf = BenchmarkConfig(benchmark_conf_path, workload_name=None, db_profile=db_setup)
    setup_fabric_env(conf)

    db_handler = {
        'cassandra': setup_cassandra
    }

    execute(db_handler[db_profile], conf)


@task
@runs_once
def db_setup(benchmark_conf_path=BENCHMARK_CONF_PATH, db_profile=None):
    """Setups database.
       Params:
           benchmark_conf_path: path to benchmark config if YAML format
           db_profile: database profile
    """
    check_arg_not_blank(benchmark_conf_path, 'benchmark_conf_path')
    check_arg_not_blank(db_profile, 'db_profile')

    conf = BenchmarkConfig(benchmark_conf_path, workload_name=None, db_profile=db_setup)
    setup_fabric_env(conf)

    db_handler = {
        'cassandra': setup_cassandra
    }

    execute(db_handler[db_profile], conf)
