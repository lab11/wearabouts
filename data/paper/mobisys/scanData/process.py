#!/usr/bin/env python3

import json
import sys
import os
import glob
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

    # grab data
    x = infile.split('_')[0][1:]
    y = infile.split('_')[1][1:]
    data.append([
            x,
            y,
            pkts[-1]['rssi']
            ])

# print data to file
outfile = "rssis.data"
dataprint.to_newfile(outfile, data, overwrite=True)
print(str(outfile) + " created")

