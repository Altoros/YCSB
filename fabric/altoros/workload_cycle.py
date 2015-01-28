# Describes full workload running cycle.
# Serj Sintsov, 2015
#
from fabric.api import env
from fabric.api import execute
from fabric.api import parallel
from fabric.api import run
from fabric.api import runs_once
from fabric.api import task

import errno, sys


HOSTS_FILE = 'dbhosts'


def fault(msg):
        print "Error: %s" % msg 
        sys.exit(errno.EIO)

        
def check_arg_not_blank(arg):
    if not arg:
        fault("Expected not blank argument")


def init_hosts():
    try:
        with open(HOSTS_FILE, 'r') as f:
            hosts = []
            for line in f:
                line = line.strip()
                if len(line) > 0:
                    hosts.append(line)
                    
            env.roledefs['db'] = hosts
            
    except IOError as e:
        fault( "can not read hosts file '%s': %s" % (HOSTS_FILE, e.strerror) ) 

                    
def init():
    init_hosts() 


def get_start_workload_cmd(workload_name):
    return 'sleep 5 && echo %s' % workload_name


def start_workload(workload_name):
    return run( get_start_workload_cmd(workload_name) )


@task
@runs_once
@parallel
def test(workload_name):
    '''Starts the whole cycle for specified workload.
       Params: <workload_name>
    '''
    check_arg_not_blank(workload_name)
    init()
    execute( start_workload, workload_name, hosts=env.roledefs['db'] )    


@task
@runs_once
@parallel
def deploy(workload_name):
    '''Deploys specified workload bundle to remote machines.
       Params: <workload_name>
    '''
    check_arg_not_blank(workload_name)
    init()    

