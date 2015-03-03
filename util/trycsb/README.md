#Local dependencies
    python 2.7.*
    pip
    
    pip2 install fabric  
    pip2 install pyyaml  
      
Or use virtualenv. 

#Remote dependencies
    Ubuntu

#Database setup

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
