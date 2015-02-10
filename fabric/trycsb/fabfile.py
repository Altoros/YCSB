# Unite all test cycles in one place
#
from lib.setup_cycle import env_setup
from lib.setup_cycle import db_setup

from lib.benchmark_cycle import deploy_benchmark
from lib.benchmark_cycle import run_benchmark

import var_tasks