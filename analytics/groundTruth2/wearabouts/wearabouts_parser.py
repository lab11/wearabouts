#!/usr/bin/env python

import dataprint
import json
import time

infile = open('wearabouts_raw.pkts', 'r')
outfile = open('wearabouts_parsed.dat', 'w')

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

# keep a dict of present_since times and locations for each person. Used to
#   determine when change events have occurred
people_dict = {}
for name in people_list:
    people_dict[name] = {'present_since': 0, 'location_id': -1}

# parse data from file
# goal is to take the raw file and turn it into a data point at each minute, with data for each name
# also check file for errors while you're parsing it
for line in infile:
    line_num += 1

    data = json.loads(line)

    # only grab 'person' type entries
    if data['type'] != 'person':
        continue

    # adkinsjd -> sairohit
    if data['uniqname'] == 'adkinsjd':
        data['uniqname'] = 'sairohit'
    person = data['uniqname']

    # error check
    if data['present_since'] == 0:
        if (person in people_dict and people_dict[person]['location_id'] != -1
                and prev_diff_seconds > 0):
            print("Error. Data reset while running. Line " + str(line_num))
            break
        #if data['uniqname'] not in ['cfwelch']:
        #    print("Skipping data present since 0 at line " + str(line_num) + '\t\t' + str(line))
        continue
    if data['uniqname'] not in people_dict:
        if data['uniqname'] not in ['cfwelch']:
            print("Unhandled person: " + str(data['uniqname']))
        # don't break here. Just move on
        continue

    # check if this record is a new event
    if (people_dict[person]['location_id'] == data['location_id']):
        # stale data
        continue

    # update person
    people_dict[person]['present_since'] = data['present_since']
    people_dict[person]['location_id'] = data['location_id']

    # generate time data for this line
    curr_time = time.strftime('%H:%M:%S', time.localtime(data['present_since']))
    diff_seconds = float(data['present_since']) - start_timestamp
    time_data = [curr_time, diff_seconds]
    # error check
    if diff_seconds < prev_diff_seconds:
        print("Backwards timestamp, Line: " + str(line_num))
        break
    prev_diff_seconds = diff_seconds

    # generate locations for this line
    truth_data = []
    for name in people_list:
        truth_data.append(int(people_dict[name]['location_id']))

    # record data
    out_data.append(time_data+truth_data)
else:
    print("Complete!")


# print data to file
dataprint.to_file(outfile, out_data)

infile.close()
outfile.close()

