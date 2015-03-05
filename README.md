wearabouts
===========

Semantic heuristic localization

Requires:
 * fitbit wireless sync dongle
 * people wearing fitbits

All fitbits need to be identified so people and fitbit IDs can be correlated
data is stored to and pulled from [GATD](https://github.com/lab11/gatd)


## Fitbitfinder Installation steps
1. Install galileo, a python utility for interacting with fitbits, and other python libraries
    `sudo pip install galileo IPy socketIO-client`

2. Modify usb permissions
    `sudo cp 99-fitbit.rules /etc/udev/rules.d/99-fitbit.rules`

3. Remove and re-insert Fitbit dongle

4. Run fitbitfinder
    `./fitbitfinder.py`

## MacScanner Installation steps
1. Install scapy python library
    `cd /tmp`
    `wget http://www.secdev.org/projects/scapy/files/scapy-latest.tar.gz`
    `tar zxvf scapy-latest.tar.gz`
    `cd scapy-2.*`
    `sudo python setup.py install`

2. Run macScanner
    `sudo ./macScanner.py`


## Weareabouts Installation steps
1. Create a virtual environment
    `sudo pip install virtualenv`
    `virtualenv venv`

2. Start the virtual environment
    `source venv/bin/activate`

3. Install IPy and socketIO-client to virtual environment
    `pip install IPy socketIO-client`

4. Replace init file from socketIO-client
    `cp socketIO_client__init__.py venv/lib/python2.7/site-packages/socketIO_client/__init__.py`

5. Run wearabouts
    `./whereabouts.py`



SwarmBox Wearabouts
-------------------

Running Wearabouts in a local context requires:

1. A central RabbitMQ server that handles queuing and distributing data
between applications.

    To set this up using Docker:

        docker run -d -p 5672:5672 -p 15672:15672 tutum/rabbitmq

    Then run:

        docker ps

    to get the container ID. Now to figure out the password that the RabbitMQ
    admin user was assigned:

        docker logs <container id>


    Now configure the RabbitMQ instance using the web interface:

        http://host:15672

    Add a new vhost, a user for that vhost, and add the admin user to the
    vhost. Finally, we need to add a topic exchange to the vhost.


2. A central Wearabouts instance that is making determinations about where
people are.

3. Many BLE (and other) scanner applications that are looking for packets
from devices.

    For the node.js based scanner:

        sudo apt-get install bluetooth bluez-utils libbluetooth-dev
        cd bleScanner
        npm install
        sudo node NOBLE_REPORT_ALL_HCI_EVENTS=1 bleScanner.js


