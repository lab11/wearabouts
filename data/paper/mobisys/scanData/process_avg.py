#!/usr/bin/env python3

import json
import sys
import os
import glob
import math
import dataprint

# get input file
files = glob.glob('x*_y*')

# create data array
data = []
data.append(['x', 'y', 'rssi'])

for infile in files:
    print("Processing file " + str(infile))

    # get pkts from json
    pkts = []
    with open(infile) as f:
        for line in f:
            pkts.append(json.loads(line))

    # create averaged RSSI
    rssis = []
    for pkt in pkts:
        rssis.append(pkt['rssi'])

    # find median
    avg_rssi = 0
    srtd = sorted(rssis)
    mid = int(math.floor(len(rssis)/2))
    if len(rssis)%2 == 0:
        # take the average of the middle two
        avg_rssi = int(round((srtd[mid-1] + srtd[mid]) / 2.0))
    else:
        # return the middle value
        avg_rssi = int(round(srtd[mid]))

    # grab data
    x = infile.split('_')[0][1:]
    y = infile.split('_')[1][1:]
    data.append([
            x,
            y,
            avg_rssi
            ])

# print data to file
outfile = "rssis_avg.data"
dataprint.to_newfile(outfile, data, overwrite=True)
print(str(outfile) + " created")

