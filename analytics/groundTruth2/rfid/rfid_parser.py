#!/usr/bin/env python

import dataprint
import json
import time

infile = open('rfid_raw.pkts', 'r')
outfile = open('rfid_parsed.dat', 'w')

out_data = []
out_data.append(['#time', 'seconds', 'samkuo', 'brghena', 'azhen', 'bradjc', 'wwhuang', 'ppannuto', 'sdebruin', 'bpkempke', 'mclarkk', 'rohitram', 'tzachari', 'nklugman', 'sairohit'])

people_list = ['samkuo', 'brghena', 'azhen', 'bradjc', 'wwhuang', 'ppannuto', 'sdebruin', 'bpkempke', 'mclarkk', 'rohitram', 'tzachari', 'nklugman', 'sairohit']
start_hour = 18
start_min = 27
start_sec = 43
start_timestamp = 1441060063

line_num = 0
error = False
prev_diff_seconds = -100000
curr_day = 0
curr_hour = start_hour
curr_min = start_min
curr_sec = start_sec
truth_data = []

# parse data from file
# goal is to take the raw file and turn it into a data point at each minute, with data for each name
# also check file for errors while you're parsing it
for line in infile:
    line_num += 1

    data = json.loads(line)

    # generate time data for this line
    curr_time = time.strftime('%H:%M:%S', time.localtime(data['timestamp']))
    diff_seconds = int(float(data['timestamp']) - start_timestamp)
    time_data = [curr_time, diff_seconds]
    # error check
    if diff_seconds < prev_diff_seconds:
        print("Backwards timestamp, Line: " + str(line_num))
        break
    prev_diff_seconds = diff_seconds

    # generate locations for this line
    truth_data = []
    for name in people_list:
        if name in data['people']:
            truth_data.append(int(data['people'][name]['location_id']))
        else:
            truth_data.append(-1)
    # error check
    for name in data['people']:
        if name not in people_list:
            print("Error, unknown person: " + str(name))
            error = True
            break
    if error:
        break

    # record data
    out_data.append(time_data+truth_data)
else:
    print("Complete!")


# print data to file
dataprint.to_file(outfile, out_data)

infile.close()
outfile.close()

