# Unite all test cycles in one place
#
from lib.setup_cycle import setup_db
from lib.setup_cycle import setup_env

from lib.benchmark_cycle import deploy_benchmark
from lib.benchmark_cycle import run_benchmark

import var_tasks
