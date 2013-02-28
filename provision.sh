#!/bin/bash
export DEBIAN_FRONTEND=noninteractive

# Update
apt-get update

# Basic Packages
apt-get install -y build-essential
apt-get install -y curl
apt-get install -y git-core
apt-get install -y htop
apt-get install -y libevent-dev
apt-get install -y make
apt-get install -y pep8
apt-get install -y pyflakes
apt-get install -y python-dev
apt-get install -y python-setuptools

easy_install pip

# Redis
apt-get install -y redis-server

echo "

Provisioning Complete. CTRL+C if this shows for more than a few seconds...

"
