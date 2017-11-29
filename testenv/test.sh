#!/bin/bash

sudo killall agent.py

#apt-get update

apt-get install -q -y screen htop vim curl wget git python-pip
apt-get install -q -y rabbitmq-server

sudo -E pip install -U pip pika enum34 GitPython

# RabbitMQ Plugins
service rabbitmq-server stop
rabbitmq-plugins enable rabbitmq_management
rabbitmq-plugins enable rabbitmq_jsonrpc
service rabbitmq-server start

rabbitmq-plugins list

sudo chmod 0777 /opt

if [ ! -d "/etc/capdet" ]; then
	sudo mkdir /etc/capdet
	sudo chmod 0777 /etc/capdet
fi

ip=$(ifconfig eth1 | grep "inet addr:" | awk '{print $2}' | cut -d':' -f2)
echo "$ip"

echo "[server]" > /etc/capdet/capdet.cfg
echo "address = 10.91.53.4" >> /etc/capdet/capdet.cfg
echo "[agent]" >> /etc/capdet/capdet.cfg
echo "address = $ip" >> /etc/capdet/capdet.cfg

if [ ! -d "/var/log/CapDet" ]; then
	sudo mkdir /var/log/CapDet
	sudo chmod 0777 /var/log/CapDet
fi

if [ ! -d "/var/lib/CapDet" ]; then
        sudo mkdir /var/lib/CapDet
        sudo chmod 0777 /var/lib/CapDet
fi

if [ -d "/home/vagrant/CapDet" ]; then
	cd /home/vagrant/CapDet; git checkout WIP1; git pull
else
	cd /home/vagrant/; git clone https://github.com/SzymonGraczyk/CapDet.git /home/vagrant/CapDet
fi

echo "Start agent"
/home/vagrant/CapDet/agent.py -vv &
