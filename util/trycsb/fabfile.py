"""Publish fabric tasks
"""
from lib.setup_cycle import setup_db
from lib.setup_cycle import setup_env

from lib.benchmark_cycle import benchmark_deploy
from lib.benchmark_cycle import benchmark_run
from lib.benchmark_cycle import benchmark_drop_logs

import var_tasks