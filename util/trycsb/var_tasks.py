"""Variable scripts. Used to start/stop/kill services and process,
   update configs from test to test
"""
from fabric import state
from fabric.api import env
from fabric.api import execute
from fabric.api import get
from fabric.api import hide
from fabric.api import parallel
from fabric.api import roles
from fabric.api import run
from fabric.api import runs_once
from fabric.api import sudo
from fabric.api import settings
from fabric.api import task

from lib.util import check_arg_not_blank
from lib.util import tar

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
@roles('servers', 'clients')
def _virgin_servers_for_all():
    with settings(warn_only=True):
       sudo('service mysql stop')
       sudo('service apache2 stop')
       sudo('service bind9 stop')
       sudo('killall -s 15 sar')
       sudo('killall -s 15 mongos')
       sudo('killall -s 15 mongod')
       sudo('service couchbase-server stop')
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
        sudo('killall -s 15 sar')
        sudo('killall -s 15 mongos')
        sudo('killall -s 15 java')
        sudo('echo "echo 1 > /proc/sys/vm/drop_caches" | sudo sh')


@roles('servers')
def _virgin_servers_for_cassandra():
    sudo('blockdev --setra 128 /dev/sda6')
    sudo('blockdev --setra 128 /dev/sdb1')
    sudo('swapoff --all')

    #sudo('rm -f /var/log/datastax-agent/*.log')
    sudo('rm -f /var/log/cassandra/*.log')
    time.sleep(randint(1, 10))
    sudo('service cassandra start')
    #time.sleep(10)
    #run('nodetool -h %s setcachecapacity -- 128 0 50' % state.env['host'])
    #sudo('sed -i "s|concurrent_reads: 16 # changed|concurrent_reads: 48 # changed|g" /etc/cassandra/cassandra.yaml')
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
        if virgin_clients_handlers.get(db_profile):
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
    _setup_fabric_env(conf)

    execute(_do_reboot_machines)


@task
def copy_system_confs():
    get('/etc/fstab')
    get('/etc/sysctl.conf')


@roles('servers', 'clients')
def _do_benchmark_copy_logs(src_dir, workload_name, date_str):
    with settings(warn_only=True):
        get(tar(src_dir, '%s-stats__%s__%s.log' % (workload_name, state.env['host'], date_str)))
        get(tar(src_dir, '%s__%s__%s.log' % (workload_name, state.env['host'], date_str)))


@task
@runs_once
def benchmark_copy_logs(config_path=BENCHMARK_CONF_PATH, src_dir=None, workload_name=None, date_str=None):
    conf = BenchmarkConfig(config_path)
    _setup_fabric_env(conf)
    execute(_do_benchmark_copy_logs, src_dir, workload_name, date_str)


@roles('servers')
def _do_cassandra_copy_logs(workload_name, keyspace):
    cfg_dir = '/etc/cassandra/'
    logs_dir = '/var/log/cassandra'
    log = 'system.log'
    table = '%s.test_table' % keyspace
    workload = workload_name
    prefix = '%s__%s' % (workload, state.env['host'])

    with settings(warn_only=True):
        cfstats_out = '%s__cfstats.txt' % prefix
        run('nodetool cfstats %s > %s' % (table, cfstats_out))
        get(cfstats_out)
        run('rm -f ' + cfstats_out)

        tpstats_out = '%s__tpstats.txt' % prefix
        run('nodetool tpstats > %s' % tpstats_out)
        get(tpstats_out)
        run('rm -f ' + tpstats_out)

        info_out = '%s__info.txt' % prefix
        run('nodetool info > %s' % info_out)
        get(info_out)
        run('rm -f ' + info_out)

        system_out = tar(logs_dir, log,  '%s__%s.tar' % (prefix, log))
        get(system_out)
        sudo('rm -f ' + system_out)

        cassandra_yaml = 'cassandra.yaml'
        cassandra_env = 'cassandra-env.sh'

        get(cfg_dir + cassandra_yaml, '%(host)s/' + prefix + '__' + cassandra_yaml)
        get(cfg_dir + cassandra_env, '%(host)s/' + prefix + '__' + cassandra_env)


@task
@runs_once
def cassandra_copy_logs(config_path=BENCHMARK_CONF_PATH, workload_name=None, keyspace=None):
    conf = BenchmarkConfig(config_path)
    _setup_fabric_env(conf)
    execute(_do_cassandra_copy_logs, workload_name, keyspace)


@roles('servers')
def _do_cassandra_set_cache():
    conf = '/etc/cassandra/cassandra.yaml'
    #sudo('sed -i "s|commitlog_sync: batch # changed|commitlog_sync: batch # changed|g" %s' % conf)
    #sudo('sed -i "s|commitlog_sync_batch_window_in_ms: 1 # changed|commitlog_sync_batch_window_in_ms: 1 # changed|g" %s' % conf)
    #sudo('sed -i "s|commitlog_sync: periodic # changed|#commitlog_sync: periodic # changed|g" %s' % conf)
    #sudo('sed -i "s|commitlog_sync_period_in_ms: 5000 # changed|#commitlog_sync_period_in_ms: 5000 # changed|g" %s' % conf)
    sudo('sed -i "s|trickle_fsync: true # changed|trickle_fsync: false|g" %s' % conf)

    #run('nodetool setcachecapacity -- 128 512 50')


@task
@runs_once
def cassandra_set_cache(config_path=BENCHMARK_CONF_PATH):
    conf = BenchmarkConfig(config_path)
    _setup_fabric_env(conf)
    execute(_do_cassandra_set_cache)


@task
def cassandra_copy_confs():
    get('/etc/cassandra/cassandra.yaml')


@task
@runs_once
def rm_mongodb_data(config_path=BENCHMARK_CONF_PATH):
    conf = BenchmarkConfig(config_path)
    _setup_fabric_env(conf)
    execute(_do_rm_mongodb_data)


@roles('servers')
def _do_rm_mongodb_data():
    sudo("rm -rf /disk1/mongodb-data/config/*")
    sudo("rm -rf /disk1/mongodb-data/db/rs0/*")
    sudo("rm -rf /disk1/mongodb-data/db/rs1/*")
    sudo("rm -rf /disk1/mongodb-conf/*")
    sudo("rm -rf /mongodb-journal/*")
    sudo("rm -rf /disk1/mongodb-arb/*")

@task
def mongodb_copy_logs():
    files = ['config.log', 'rs0.log', 'rs1.log']
    for file in files:
        log = tar('/disk1/mongodb-logs', file)
        get(log)

@task
def dpkg_configure():
    sudo("dpkg --configure -a")