#Local dependencies
    python 2.7.*
    pip
    
    pip2 install fabric  
    pip2 install pyyaml  
      
Or use virtualenv.

Note that fabric scripts may not work on [Windows](https://github.com/fabric/fabric/issues/489)

#Remote dependencies
    Ubuntu


#Benchmark configuration

All YCSB settings you can find in `benchmark_conf.yaml` file.
So first you need to configure it.

#Create executable YCSB runner

How to make executable YCSB file with all necessary dependencies, please see in [readme](./../../README.md) under the root.

Don't forget to copy the result jar from `/dbs/$database/target` directory to `/util/trycsb` directory and
to specify the correct name of jar file in `uploads:` section in `benchmark_conf.yaml` file.
For example: `uploads: [cassandra-ycsb-exec.jar]`

#Deploying YCSB client on server

To deploy YCSB client on server, run:

    fab benchmark_deploy

#Environment setup

There are setup scripts under `setup_scripts/environment` directory for environment configuration (CentOS or Ubuntu).

To setup environment please issue the following commands:

    fab setup_env:env_type=client
    fab setup_env:env_type=server

#Cluster setup

Under `setup_scripts` directory you can find setup scripts for several databases (now only for Cassandra, Couchbase and MongoDB).

To setup cluster, run:

    fab setup_db:db_profile=database_profile_name

where `database_profile_name` is the name of certain database, specified in section `db_profiles` in `benchmark_conf.yaml` file.

#Run Benchmark Workloads

If you need to run only one instance of YCSB client, run:

    fab benchmark_run:workload_name=example,db_profile=database_profile_name

or if you need to run several YCSB clients, run:

    ./run_multiple_clients.sh clients_count workload_name database_profile_name

#MongoDB

To prepare your MongoDB cluster you need:

    set cluster settings in *.yaml files located in conf directory
    uncomment install_mongo.sh and setup_cluster.sh $1 in setup_mongodb.sh
    run fab setup_db:db_profile=mongodb
    run fab var_tasks.virgin_servers:db_profile=mongodb
    uncomment init_shards.sh $1 in setup_mongodb.sh
    run fab setup_db:db_profile=mongodb
    uncomment download_mongos.sh and enable-sharding.sh in setup.sh for your client
    run fab setup_env:env_type=client

#Cassandra

To configure Cassandra cluster you need:

    set DSC_VERSION and CASSANDRA_VERSION variables in setup_cassandra.sh
    configure all needed parameters in bin/cluster_setup.sh

Known issues: <br/>
[could not access pidfile for Cassandra](https://issues.apache.org/jira/browse/CASSANDRA-9822) (and possible [solution](https://github.com/locp/cassandra/issues/63#issuecomment-125328745))


#Couchbase

Couchbase requires some special configuration changes in `benchmark_conf.yaml`.

##1. Couchbase database profile:

For choosing update method use option:
**`couchbase.updateType`** default value `SYNC_CAS_LOOP`

* `SYNC_CAS_LOOP` for pessimistic concurrency
* `ASYNC_CAS_LOOP` for optimistic concurrency
* `SYNC_LOCAL_LOCK` for local locking

For update retry time use option:
**`couchbase.concurrentUpdateRetryTimeMillis`** default value `5`

For the possible disk persistence use option:
**`couchbase.persistTo`** default value `MASTER`

* `NONE`
* `MASTER`
* `ONE`
* `TWO`
* `THREE`
* `FOUR`

For the possible replication use option:
**`couchbase.replicateTo`** default value `ONE`

* `NONE`
* `ONE`
* `TWO`
* `THREE`

##2. Workload settings for Couchbase:

Performance option: **Key/Value Endpoints per Node** - *The number of actual endpoints (sockets) to open per Node in the cluster against the Key/value service*:
`kvEndpoints(int)` default `1`

Timeout option: **Key-Value Timeout** - *The Key/Value default timeout is used on all blocking operations which are performed on a specific key if not overridden by a custom timeout*:
`kvTimeout(long)` default `2500` in ms

See http://docs.couchbase.com/developer/java-2.1/env-config.html for a details.

#Virgin servers

To make servers clean, run:

    fab var_tasks.virgin_servers

#View SAR logs

As soon as the workload stops, SAR logs from servers are automatically downloaded on localhost.

Use `plot_sar.py` from `/util/plotit` directory. Run:

    python plot_sar.py --sar_log filename

where `filename` is the name of binary log file.