#!/usr/bin/env python

# Script to find fitbits
#   Returns Fitbit IDs and RSSI to the fitbit
#   Users should call discover_fitbits()
#   Can be run as a utility from shell as well
#
# Requires the galileo program
#   pip install galileo
#   https://bitbucket.org/benallard/galileo

import sys
import uuid
from ctypes import c_byte

try:
    from galileo import (PERMISSION_DENIED_HELP, FitBitDongle,
            TimeoutError, NoDongleException, PermissionDeniedException,
            FitbitClient, a2t)
except ImportError:
    print("Unable to find the Galileo Library")
    print("    sudo pip install galileo")
    exit()

def discover_fitbits():
    dongle = FitBitDongle()
    try:
        dongle.setup()
    except NoDongleException:
        print("No dongle connected, aborting")
        return
    except PermissionDeniedException:
        print(PERMISSION_DENIED_HELP)
        return

    fitbit = FitbitClient(dongle)
    fitbit.disconnect()
    fitbit.getDongleInfo()
    
    try:
        trackers = [t for t in __discovery(dongle)]

    except TimeoutError:
        print ("Timeout trying to discover trackers")
        return
    except PermissionDeniedException:
        print PERMISSION_DENIED_HELP
        return

    return trackers

def __discovery(dongle):
    dongle.ctrl_write([0x1a, 4, 0xba, 0x56, 0x89, 0xa6, 0xfa, 0xbf,
                       0xa2, 0xbd, 1, 0x46, 0x7d, 0x6e, 0, 0,
                       0xab, 0xad, 0, 0xfb, 1, 0xfb, 2, 0xfb,
                       0xa0, 0x0f, 0, 0xd3, 0, 0, 0, 0])
    dongle.ctrl_read() # StartDiscovery
    d = dongle.ctrl_read(4000)
    while d[0] != 3:
        RSSI = c_byte(d[9]).value
        yield [a2t(list(d[2:8])), 
                RSSI]
        d = dongle.ctrl_read(4000)

    # tracker found, cancel discovery
    dongle.ctrl_write([2, 5])
    dongle.ctrl_read() # CancelDiscovery

def main():
    trackers = discover_fitbits()
    if (trackers is None):
        return
    for [ID, RSSI] in trackers:
        print("ID: " + str(ID) + " RSSI: " + str(RSSI))

if __name__ == "__main__":
    main()
