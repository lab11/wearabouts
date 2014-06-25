whereabouts
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


## Whereabouts Installation steps
1. Create a virtual environment  
    `sudo pip install virtualenv`  
    `virtualenv venv`

2. Start the virtual environment  
    `source venv/bin/activate`

3. Install IPy and socketIO-client to virtual environment  
    `pip install IPy socketIO-client`

4. Replace init file from socketIO-client  
    `cp socketIO_client__init__.py venv/lib/python2.7/site-packages/socketIO_client/__init__.py`  

5. Run whereabouts  
    `./whereabouts.py`

