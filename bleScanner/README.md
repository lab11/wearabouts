BLE Scanner
===========

Uses the Nordic nrf51822 USB dongle to scan for nearby BLE devices. Uses the
nRF-Sniffer firmware on the nrf51822 to continuously receive advertising
packets and record device addresses.

Requires:
 * nrf51822 USB dongle
 * people wearing BLE devices

In order to correlate devices with people, BLE addresses need to be identified
for various devices. Data is stored to and pulled from [GATD](https://github.com/lab11/gatd)

Files in bleAPI/ were created by Nordic Semiconductor and are used with minor
modifications under the license included in the directory.

## BLE Scanner Installation steps
1. Install python libraries
    `sudo pip install pyserial socketIO-client`

2. Program nrf51822 USB dongle with nRF-Sniffer firmware (follow guide available
[here](https://www.nordicsemi.com/eng/Products/Bluetooth-Smart-Bluetooth-low-energy/nRF51822-Development-Kit)

3. Run bleScanner
    `./bleScanner.py`

