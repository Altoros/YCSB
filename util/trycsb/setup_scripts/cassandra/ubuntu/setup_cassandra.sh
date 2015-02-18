#!/bin/bash

if [ -z "$1" ]; then
    echo "Host address required"
    exit 1
fi

bash bin/uninstall_dse.sh
bash bin/install_dse.sh
bash bin/setup_configuration.sh $1