#!/usr/bin/env python3

import ast
import time


infile = open('watch_data.json', 'r')
outfile = open('unique_bins.data', 'w')

data = {}

index = 0
for line in infile:
    #index += 1
    #if index > 100000:
    #    break

    try:
        pkt = ast.literal_eval(line)
    except Exception as e:
        break
    data[pkt['time']] = pkt['ble_addr']

minutes_per_bin = 30

first = True
prev_decade = -1
bin_key = 0
ble_ids = []
unique_counts = {}
start_time = 0

for timestamp in sorted(data.keys()):
    minute = time.localtime(timestamp)[4]
    if first and minute%minutes_per_bin != 0:
        continue
    if first:
        start_time = timestamp
    first = False

    decade = int(minute/minutes_per_bin)
    if decade != prev_decade:
        prev_decade = decade
        bin_key = int(timestamp/60/minutes_per_bin)*minutes_per_bin*60
        ble_ids = []
        unique_counts[bin_key] = 0

    if data[timestamp] not in ble_ids:
        ble_ids.append(data[timestamp])
        unique_counts[bin_key] += 1

for timestamp in sorted(unique_counts.keys()):
    time_diff = timestamp - start_time
    outfile.write(str(time_diff) + ', ' + str(unique_counts[timestamp]) + '\n')
    print('(' + str(time.strftime("%H%M", time.localtime(timestamp))) + ', ' + str(time_diff) + '),')

