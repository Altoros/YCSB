"""Variable scripts. Used to start/stop/kill services and process,
   update configs from test to test
"""
from fabric.api import env
from fabric.api import execute
from fabric.api import get
from fabric.api import hide
from fabric.api import parallel
from fabric.api import roles
from fabric.api import runs_once
from fabric.api import sudo
from fabric.api import settings
from fabric.api import task

from lib.util import check_arg_not_blank

from lib.config import BenchmarkConfig

import time
from random import randint

BENCHMARK_CONF_PATH = 'benchmark_conf.yaml'


class RunLogger():

    def __init__(self):
        self._info = []

    def run(self, cmd):
        self._exec(cmd)

    def sudo(self, cmd):
        self._exec(cmd, is_sudo=True)

    @property
    def commands_out(self):
        return self._info

    def _exec(self, cmd, is_sudo=False):
        with settings(warn_only=True):
            with hide('running', 'stdout', 'stderr'):
                if is_sudo:
                    self._info.append('# %s' % cmd)
                    self._info.append(sudo(cmd))
                else:
                    self._info.append('$ %s' % cmd)
                    self._info.append(run(cmd))


class RunLogPrinter():

    def print_log(self, hosts_to_log):
        for host, log in hosts_to_log.items():
            print '###################\n%s\n###################' % host
            for l in log:
                print l

            print '\n'


def _setup_fabric_env(conf):
    conn = conf.connection_parameters

    env.user = conn.get('user')
    env.password = conn.get('password')
    env.key_filename = conn.get('key')

    env.roledefs['clients'] = conf.client_conf.hosts_addresses
    env.roledefs['servers'] = conf.server_conf.hosts_addresses


@parallel
@roles('servers')
def _virgin_servers_for_all():
    with settings(warn_only=True):
       sudo('service mysql stop')
       sudo('service apache2 stop')
       sudo('service bind9 stop')
       sudo('killall -s 15 mongod')
       sudo('service couchbase-server stop')
       sudo('killall -s 15 sar')
       sudo('service cassandra stop')
       sudo('service opscenterd stop')
       sudo('service datastax-agent stop')
       sudo('echo "echo 1 > /proc/sys/vm/drop_caches" | sudo sh')


@parallel
@roles('servers')
def _virgin_servers_for_mongodb():
    sudo('blockdev --setra 32 /dev/sda6')
    sudo('blockdev --setra 32 /dev/sdb1')
    sudo('rm -f /disk1/mongodb-logs/*.log')
    sudo('service mongod-rs0 start')
    sudo('service mongod-rs1 start')
    sudo('service mongod-rs-config start')


@parallel
@roles('clients')
def _virgin_clients_for_mongodb():
    with settings(warn_only=True):
        sudo('rm -f /disk1/mongodb-logs/*.log')
        sudo('killall -s 15 mongos')

@roles('servers')
def _virgin_servers_for_cassandra():
    sudo('blockdev --setra 128 /dev/sda6')
    sudo('blockdev --setra 128 /dev/sdb1')
    sudo('swapoff --all')

    sudo('rm -f /var/log/datastax-agent/*.log')
    sudo('rm -f /var/log/cassandra/*.log')
    time.sleep(randint(1, 10))
    sudo('service cassandra start')
    #time.sleep(3)
    #sudo('service datastax-agent start')


@parallel
@roles('servers', 'clients')
def _do_reboot_machines():
    with settings(warn_only=True):
       sudo('reboot')


@parallel
@roles('servers', 'clients')
def _view_machine_info():
    run_logger = RunLogger()
    run_logger.sudo('ifconfig')

    return run_logger.commands_out


@task
@runs_once
def virgin_servers(config_path=BENCHMARK_CONF_PATH, db_profile=None):
    check_arg_not_blank(config_path, 'config_path')

    conf = BenchmarkConfig(config_path)
    _setup_fabric_env(conf)

    virgin_servers_handlers = {
        'cassandra': _virgin_servers_for_cassandra,
        'mongodb': _virgin_servers_for_mongodb
    }

    virgin_clients_handlers = {
        'mongodb': _virgin_clients_for_mongodb
    }

    execute(_virgin_servers_for_all)

    if db_profile:
        execute(virgin_servers_handlers[db_profile])
        execute(virgin_clients_handlers[db_profile])


@task
@runs_once
def gather_machine_info(config_path=BENCHMARK_CONF_PATH):
    check_arg_not_blank(config_path, 'config_path')

    conf = BenchmarkConfig(config_path)
    _setup_fabric_env(conf)

    result = execute(_view_machine_info)

    RunLogPrinter().print_log(result)


@task
def reboot_clients_servers(config_path=BENCHMARK_CONF_PATH):
    check_arg_not_blank(config_path, 'config_path')

    conf = BenchmarkConfig(config_path)
    setup_fabric_env(conf)

    execute(_do_reboot_machines)


@task
def copy_system_confs():
    get('/etc/fstab')
    get('/etc/sysctl.conf')


@task
def copy_cassandra_confs():
    get('/etc/cassandra/cassandra.yaml')

