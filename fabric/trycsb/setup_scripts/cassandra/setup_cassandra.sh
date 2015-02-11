#!/bin/sh

echo "deb http://sergey.sintsov_altoros.com:t0VnpFpQS70Jtf0@debian.datastax.com/enterprise stable main" | sudo tee -a /etc/apt/sources.list.d/datastax.sources.list
curl -L https://debian.datastax.com/debian/repo_key | sudo apt-key add -
apt-get update
apt-get install dse-full
apt-get install opscenter
