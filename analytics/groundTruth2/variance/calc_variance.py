#!/usr/bin/env python

import sys
import dataprint
import time
import glob

durations = range(10,1000)

#infile = open('brghena_ble.dat', 'r')
#infile = open('sairohit_ble.dat', 'r')
infile = open('sdebruin_ble.dat', 'r')

input_data = infile.readlines()
outfile = open('variance.dat', 'w')
out_data = []
out_data.append(["#duration", "variance"])
out_data += [[x] for x in durations]

start_point = 0
for start_point in range(0, len(input_data), 200):
    for duration in durations:
        rssi_data = []
        start_time = 0
        for line in input_data[start_point:]:
            if line[0] == '#':
                continue

            # import data
            data = line.split()
            timestamp = float(data[0])/1000
            rssi = float(data[1])
            #rssi = float(data[3])
            if rssi == -200:
                continue

            # get start time
            if start_time == 0:
                start_time = timestamp

            # append to dataset if within time
            if (timestamp-start_time) < duration:
                rssi_data.append(rssi)
            else:
                break
        else:
            print("Out of time")
            break

        # calculate variance for the data
        average = sum(rssi_data)/len(rssi_data)
        numerators = [(value-average)**2 for value in rssi_data]
        variance = 0
        try:
            variance = sum(numerators)/(len(rssi_data)-1)
        except ZeroDivisionError:
            print("ZeroDivisionError - Duration: " + str(duration) + '\tData: ' + str(rssi_data))

        # append to output
        out_data[durations.index(duration)+1].append(variance)

dataprint.to_file(outfile, out_data)
outfile.close()

