#!/bin/sh


# install pip 
python --version
pip --version
sudo apt-get install python-pip python-dev build-essential
sudo pip install --upgrade pip 
pip --version

# install pipenv
pip install pipenv

# install python requests
pipenv install requests

# install bitcoin core to run full node
wget https://bitcoin.org/bin/bitcoin-core-0.16.1/bitcoin-0.16.1-x86_64-linux-gnu.tar.gz
tar -xzf bitcoin-0.16.1-x86_64-linux-gnu.tar.gz
cd bitcoin-0.16.1/bin/

# run bitcoin daemon
./bitcoind

# run bitcoin client
./bitcoin-cli

# check raw blockchain files 
cd ~/.bitcoin/blocks/
