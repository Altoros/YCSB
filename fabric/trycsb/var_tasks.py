"""Variable scripts. Used to start/stop/kill services and process,
   update configs from test to test
"""
from fabric.api import env
from fabric.api import execute
from fabric.api import get
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
def virgin_servers_for_mongo():
    sudo('service mysql stop')
    sudo('service apache2 stop')
    sudo('service bind9 stop')
    sudo('service mongod start')
    sudo('service counchbase-server stop')
    sudo('service dse stop')

        
@parallel
@roles('servers')
def virgin_servers_for_cassandra():
    sudo('service mysql stop')
    sudo('service apache2 stop')
    sudo('service bind9 stop')
    sudo('service mongod stop')
    sudo('service counchbase-server stop')
    sudo('service dse start')
   

virgin_servers_handlers = {
    'cassandra': virgin_servers_for_cassandra,
    'mongo': virgin_servers_for_mongo
}

    
@task
@runs_once
def virgin_servers(config_path=BENCHMARK_CONF_PATH, db_profile=None):
    check_arg_not_blank(config_path, 'config_path')
    check_arg_not_blank(db_profile, 'db_profile')
 
    conf = BenchmarkConfig(benchmark_conf_path)
    setup_fabric_env(conf)

    execute(virgin_servers_handlers[db_profile])


@task
def copy_cassandra_confs():
    get('/etc/dse/cassandra/cassandra.yaml')
    get('/etc/dse/cassandra/cassandra-env.sh')
    get('/etc/dse/cassandra/commitlog_archiving.properties')
    get('/etc/default/dse')
