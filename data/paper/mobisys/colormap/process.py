#!/usr/bin/env python3

import json
import sys
import os
import dataprint

# get input file
if not len(sys.argv) >= 2:
    print("Need input file")
    sys.exit(1)

for infile in sys.argv[1:]:
    outfile = str(os.path.splitext(infile)[0]) + ".data"
    print("Processing file " + str(infile))

    # get pkts from json
    pkts = []
    with open(infile) as f:
        for line in f:
            pkts.append(json.loads(line))

    # grab initial data
    starttime = pkts[0]['time']

    # create data from pkts
    data = []
    data.append(['time', 'height', 'rssi'])
    index = 0
    for pkt in pkts:
        data.append([
                pkt['time']-starttime,
                index,
                pkt['rssi']
                ])
        index += 1

    # print data to file
    dataprint.to_newfile(outfile, data, overwrite=True)
    print(str(outfile) + " created")

