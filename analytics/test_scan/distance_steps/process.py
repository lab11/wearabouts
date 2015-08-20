#!/usr/bin/env python3

import math
import json
import sys
import os
import glob
import dataprint

# create data array
timedata = []
timedata.append(['#distance', 'packetpersecond'])
rssidata = []
rssidata.append(['#distance', 'rssi'])

files = [('30cm.dat', 0.3), ('1m.dat', 1), ('2m.dat', 2), ('5m.dat', 5), ('10m.dat', 10), ('15m.dat', 15), ('20m.dat', 20)]

for (infile,distance) in files:
    print("Processing file " + str(infile))

    # get pkts from json
    pkts = []
    with open(infile) as f:
        for line in f:
            if line[0] == '#':
                continue

            pkts.append(line.split())
            rssidata.append([distance, line.split()[1]])

    #if distance == 20:
    #    prev_time = float(pkts[0][0])
    #    for pkt in pkts[1:]:
    #        print(float(pkt[0])-prev_time)
    #        prev_time = float(pkt[0])

    # grab data
    packet_rate = len(pkts)/(float(pkts[-1][0])-float(pkts[0][0]))
    timedata.append([distance, packet_rate])

# print data to file
outfile = "times.data"
dataprint.to_newfile(outfile, timedata, overwrite=True)
print(str(outfile) + " created")
outfile = "rssis.data"
dataprint.to_newfile(outfile, rssidata, overwrite=True)
print(str(outfile) + " created")

