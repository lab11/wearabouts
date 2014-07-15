#!/usr/bin/env python2

# I want to plot rssi values along with labels for each uniqname for 4908 and 4670

import json
import ast
import time

labmates = ['brghena', 'samkuo', 'ppannuto', 'bradjc', 'wwhuang', 'tzachari', 'None']

def cur_datetime(time_num):
    return time.strftime("%m/%d/%Y %H:%M", time.localtime(time_num/1000))

data_dict = {}

previous_time = 0
with open('4908.data') as f:
    for line in f:
        loaded_data = ast.literal_eval(line)

        if previous_time > loaded_data['time']:
            print("Data out of order!!")
            exit()
        previous_time = loaded_data['time']

        if 'uniqname' not in loaded_data:
            continue

        # keep only labmates
        if loaded_data['uniqname'] not in labmates:
            continue
        
        # save samples of None
        if loaded_data['uniqname'] == 'None':
            loaded_data['rssi'] = -80
        
        # check rssi to see if we should save this one
        if 'rssi' not in loaded_data:
            continue
        if loaded_data['rssi'] == 0:
            continue
        if loaded_data['rssi'] == 63:
            continue

        # only use data from Monday 7:35pm to Wednesday 7:30pm
        if loaded_data['time'] < 1404776100000:
            continue
        if loaded_data['time'] > 1404948600000:
            continue

        # truncate timestamp down to 1 minute
        timestamp = int((loaded_data['time'] / 1000) / 60) * 60 * 1000
        time_str = cur_datetime(timestamp)

        # add to data
        if timestamp not in data_dict:
            data_dict[timestamp] = []

        #XXX: This might leave empty sets
        if loaded_data['rssi'] < -83:
            continue

        data_dict[timestamp].append(loaded_data['uniqname'])

#for timestamp in sorted(data_dict.keys()):
#    print(cur_datetime(timestamp) + '\t' + str(timestamp))
#exit()

for timestamp in range(1404776100000, 1404948600000, 300000):
    previous_time = 0
    for recorded_time in sorted(data_dict.keys()):
        if recorded_time > timestamp:
            break
        previous_time = recorded_time

    if previous_time == 0:
        print(cur_datetime(timestamp) + ':  ' + "[u'None']")
    else:
        if len(data_dict[previous_time]) == 0:
            print(cur_datetime(timestamp) + ':  ' + "[u'None']")
        else:
            print(cur_datetime(timestamp) + ':  ' + str(data_dict[previous_time]))

exit()

