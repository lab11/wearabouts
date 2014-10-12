fitbitfinder
============

Uses the fitbit base station dongle to scan for nearby fitbits. Can run scans
periodically or use a door open event to trigger scans.

Note: This program is legacy code and no longer in active use. It has been
replaced by [bleScanner](../bleScanner)

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

