Yahoo! Cloud System Benchmark (YCSB)
====================================

A note on comparing multiple systems
------------------------------------

NoSQL systems have widely varying defaults for trading off write durability vs performance.  Make sure that you are [comparing apples to apples across all candidates](http://www.datastax.com/dev/blog/how-not-to-benchmark-cassandra-a-case-study).  The most useful common denominator is synchronously durable writes.  The following YCSB clients have been verified to perform synchronously durable writes by default:

- Couchbase
- HBase
- MongoDB

Cassandra requires a configuration change in conf/cassandra.yaml.  Uncomment these lines:

    # commitlog_sync: batch
    # commitlog_sync_batch_window_in_ms: 50

Links
-----
http://research.yahoo.com/Web_Information_Management/YCSB/  
ycsb-users@yahoogroups.com  

Getting Started
---------------

###Download the latest project version:

    git clone https://github.com/Altoros/YCSB

###Create an executable YCSB runner using Maven:

    mvn package -P db_profile_id

  where `db_profile_id` is the id of database profile, specified in `pom.xml` of certain database at `/dbs` directory.
  For example:

    mvn package -P cassandra-exec

###Run YCSB command.

  How to configure environment and cluster please see [here](./util/trycsb/README.md)

  See https://github.com/brianfrankcooper/YCSB/wiki/Core-Properties for
  the list of available workload properties.

