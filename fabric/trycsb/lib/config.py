# Benchmark configs decription.
# Serj Sintsov, 2015
#
from util import fault
from util import path
from util import not_empty

import yaml
import copy


class BenchmarkConfig():
    _CURRENT_DIR = '.'

    def __init__(self, config_path, workload_name=None, db_profile=None):
        self._workload_name = workload_name
        self._db_profile = db_profile

        self._conf = BenchmarkConfig.parse_config(config_path)
        self._client_conf = ClientConfig(self, self._conf['clients'])
        self._server_conf = ServerConfig(self, self._conf['servers'])

    @classmethod
    def parse_config(cls, src):
        try:
            f = open(src, 'r')
            return yaml.load(f)

        except IOError as e:
            fault( "can not read hosts file '%s': %s" % (src, e.strerror) )

    @classmethod
    def hosts_to_addresses(cls, conf):
        return map(lambda h: h['addr'], conf.get('hosts'))

    @property
    def connection_parameters(self):
        return self._conf.get('connection')

    @property
    def benchmark_home_dir(self):
        return not_empty( self._conf['remote_home_dir'], self._CURRENT_DIR )

    @property
    def benchmark_local_home_dir(self):
        return not_empty( self._conf['local_home_dir'], self._CURRENT_DIR )

    @property
    def db_profile(self):
        return self._db_profile

    @property
    def workload_name(self):
        return self._workload_name

    @property
    def workload_local_logs_dir(self):
        local_logs_dir = not_empty(self._conf['local_logs_dir'], self._CURRENT_DIR)
        return path(self.benchmark_local_home_dir, local_logs_dir, self.db_profile)

    @property
    def workload_logs_dir(self):
        remote_logs_dir = not_empty(self._conf['remote_logs_dir'], self._CURRENT_DIR)
        return path(self.benchmark_home_dir, remote_logs_dir, self.workload_name)

    @property
    def client_conf(self):
        return self._client_conf

    @property
    def server_conf(self):
        return self._server_conf

    @property
    def options(self):
        return copy.deepcopy(self._conf)


class ClientConfig():

    def __init__(self, base_conf, cli_conf):
        self._base_conf = base_conf
        self._cli_conf  = cli_conf

        self._validate_benchmark_settings()
        self._validate_db_settings()

    def _validate_benchmark_settings(self):
        if self._base_conf.workload_name and not self.workload_parameters:
            fault("No options for workload '%s'" % self._base_conf.workload_name)

    def _validate_db_settings(self):
        if self._base_conf.db_profile and not self.db_profile_parameters:
            fault("No options for db profile '%s'" % self._base_conf.db_profile)

    @property
    def hosts_addresses(self):
        return map(lambda h: h['addr'], self._cli_conf.get('hosts'))

    @property
    def ycsb_executable_name(self):
        return self._cli_conf['ycsbexe']

    @property
    def db_profile_parameters(self):
        return self._cli_conf.get('db_profiles')[self._base_conf.db_profile]

    @property
    def workload_parameters(self):
        return self._cli_conf.get('workloads')[self._base_conf.workload_name]

    @property
    def bundles(self):
        return self._cli_conf.get('bundles')


class ServerConfig():

    def __init__(self, base_conf, srv_conf):
        self._base_conf = base_conf
        self._srv_conf  = srv_conf

    @property
    def hosts_addresses(self):
        return BenchmarkConfig.hosts_to_addresses(self._srv_conf)
