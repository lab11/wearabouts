MAC Scanner
===========

Detects nearby wireless devices. Uses a wifi interface in promiscuous mode to
sniff 802.11 packets across all channels and record MAC addresses. Runs scans
continuously, hopping across channels.

Requires:
 * wireless interface capable of promiscuous scanning (currently using the
AWUS051NH connected through USB)
 * 802.11 wireless devices, such as smartphones or laptops

In order to identify people from their devices, MAC addresses of devices need
to be identified. Data is stored to and pulled from [GATD](https://github.com/lab11/gatd)


## MacScanner Installation steps
1. Install scapy python library  
    `cd /tmp`  
    `wget http://www.secdev.org/projects/scapy/files/scapy-latest.tar.gz`  
    `tar zxvf scapy-latest.tar.gz`  
    `cd scapy-2.*`  
    `sudo python setup.py install`

2. Run macScanner  
    `sudo ./macScanner.py`

