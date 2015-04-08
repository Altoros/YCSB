"""Benchmark configs decription.

   Serj Sintsov, 2015
"""
from util import fault
from util import path
from util import not_empty

import yaml
import copy

from os import listdir
from os.path import isfile


def _parse_yaml(src):
    try:
        f = open(src, 'r')
        return yaml.load(f)

    except IOError as e:
        fault( "can not read hosts file '%s': %s" % (src, e.strerror) )


def _script_names(src_dir):
    if not src_dir:
        return []

    is_script = lambda f: isfile(path(src_dir, f)) and f.endswith('.sh')
    
    return [f for f in listdir(src_dir) if is_script(f)]


def _to_file_paths(prefix_path, file_names):
    return map(lambda n: path(prefix_path, n), file_names)


def _check_path_without_tilda(path):
    if path.startswith('~'):
        fault('Specify %s without tilda' % path)


class BenchmarkConfig():
    _CURRENT_DIR = '.'

    def __init__(self, config_path=None, workload_name=None, db_profile=None):
        self._workload_name = workload_name if workload_name else ''
        self._db_profile = db_profile if db_profile else ''

        self._conf = _parse_yaml(config_path)

        _check_path_without_tilda(self.benchmark_remote_home_dir)
        _check_path_without_tilda(self.benchmark_remote_logs_dir)

        self._client_conf = _ClientConfig(self, self._conf['clients'])
        self._server_conf = _ServerConfig(self, self._conf['servers'])


    @property
    def connection_parameters(self):
        return self._conf.get('connection')

    @property
    def benchmark_remote_home_dir(self):
        return not_empty(self._conf['benchmark_remote_home_dir'], self._CURRENT_DIR)

    @property
    def benchmark_remote_logs_dir(self):
        remote_logs_dir = not_empty(self._conf['benchmark_remote_logs_dir'], self._CURRENT_DIR)
        return path(self.benchmark_remote_home_dir, remote_logs_dir, self.db_profile)

    @property
    def benchmark_local_home_dir(self):
        return not_empty(self._conf['benchmark_local_dir'], self._CURRENT_DIR)

    @property
    def benchmark_local_logs_dir(self):
        return path(self.benchmark_local_home_dir, self.db_profile)

    @property
    def db_profile(self):
        return self._db_profile

    @property
    def workload_name(self):
        return self._workload_name

    @property
    def client_conf(self):
        return self._client_conf

    @property
    def server_conf(self):
        return self._server_conf


class _ClientConfig():

    def __init__(self, base_conf, cli_conf):
        self._base_conf = base_conf
        self._cli_conf  = cli_conf

    @property
    def hosts_addresses(self):
        return self._cli_conf.get('hosts')

    @property
    def ycsb_executable_name(self):
        return self._cli_conf['ycsbexe']

    @property
    def db_parameters(self):
        return self._cli_conf.get('db_profiles').get(self._base_conf.db_profile)

    @property
    def workload_parameters(self):
        return self._cli_conf.get('workloads').get(self._base_conf.workload_name)

    @property
    def workload_java_parameters(self):
        return not_empty(self.workload_parameters.get('java_properties'), [])

    @property
    def uploads(self):
        return self._cli_conf.get('uploads')

    @property
    def setup_local_dir(self):
        return self._cli_conf.get('setup_local_dir')

    @property
    def setup_remote_dir(self):
        return path(self._base_conf.benchmark_remote_home_dir, self._cli_conf.get('setup_remote_dir'))

    @property
    def setup_scripts_names(self):
        return _script_names(self.setup_local_dir)
        
    @property
    def setup_local_files(self):
        return _to_file_paths(self.setup_local_dir, listdir(self.setup_local_dir))

    
class _ServerConfig():

    def __init__(self, base_conf, srv_conf):
        self._base_conf = base_conf
        self._srv_conf  = srv_conf

    @property
    def hosts_addresses(self):
        return self._srv_conf.get('hosts')

    @property
    def db_parameters(self):
        return self._srv_conf.get('db_profiles').get(self._base_conf.db_profile)

    @property
    def setup_local_dir(self):
        return self._srv_conf.get('setup_local_dir')

    @property
    def setup_remote_dir(self):
        return path(self._base_conf.benchmark_remote_home_dir, self._srv_conf.get('setup_remote_dir'))

    @property
    def setup_scripts_names(self):
        return _script_names(self.setup_local_dir)
        
    @property
    def setup_local_files(self):
        return _to_file_paths(self.setup_local_dir, listdir(self.setup_local_dir))

    @property
    def setup_db_local_dir(self):
        return self.db_parameters.get('setup_local_dir')

    @property
    def setup_db_remote_dir(self):
        return path(self._base_conf.benchmark_remote_home_dir, self.db_parameters.get('setup_remote_dir'))

    @property
    def setup_db_scripts_names(self):
        return _script_names(self.setup_db_local_dir)

    @property
    def setup_db_local_files(self):
        return _to_file_paths(self.setup_db_local_dir, listdir(self.setup_db_local_dir))
