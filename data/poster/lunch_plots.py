#!/usr/bin/env python2

import json
import ast
import matplotlib.pyplot as plt

def create_hist(data_list, bins_list):
    hist = []
    for number in bins_list:
        hist.append(data_list.count(number))
    return hist

def norm_hist(hist):
    total = 0.0
    for count in hist:
        total += count

    new_hist = []
    for count in hist:
        new_hist.append(count/total)
    return new_hist

data_dict = {}
lunch_dict = {}

list_of_wednesdays = []
last_wednesday_lunch = 1400085000000
msec_in_lunch = 3600000
for num in range(52):
    list_of_wednesdays.append(last_wednesday_lunch - num*604800000)

with open('parsed_data') as f:
    for line in f:
        loaded_data = ast.literal_eval(line)

        if loaded_data['fitbit_id'] == 'None':
            continue
        if loaded_data['rssi'] >= -50:
            continue

        fitbit_id = loaded_data['fitbit_id']
        if not fitbit_id in data_dict:
            data_dict[fitbit_id] = {'data': []}
            lunch_dict[fitbit_id] = {'data': []}

        if 'uniqname' in loaded_data:
            if 'uniqname' not in data_dict[fitbit_id]:
                data_dict[fitbit_id]['uniqname'] = loaded_data['uniqname']
            if 'uniqname' not in lunch_dict[fitbit_id]:
                lunch_dict[fitbit_id]['uniqname'] = loaded_data['uniqname']

        data_dict[fitbit_id]['data'].append(loaded_data['rssi'])

        for start_time in list_of_wednesdays:
            if start_time <= loaded_data['time'] and (start_time+msec_in_lunch) >= loaded_data['time']:
                lunch_dict[fitbit_id]['data'].append(loaded_data['rssi'])

lab_members = ['brghena', 'bradjc', 'wwhuang', 'bpkempke', 'sdebruin', 'ppannuto', 'samkuo', 'mclarkk', 'adkinsjd', 'tzachari']

inlab_data = []
inlab_aggregate = []
inlab_labels = []
nolab_data = []
nolab_aggregate = []
nolab_labels = []
inlunch_data = []
for fitbit_id in data_dict:
    if 'uniqname' in data_dict[fitbit_id]:
        if data_dict[fitbit_id]['uniqname'] in lab_members:
            inlab_data.append(data_dict[fitbit_id]['data'])
            inlab_aggregate += data_dict[fitbit_id]['data']
            inlab_labels.append(data_dict[fitbit_id]['uniqname'])
            inlunch_data.append(lunch_dict[fitbit_id]['data'])
        else:
            nolab_data.append(data_dict[fitbit_id]['data'])
            nolab_aggregate += data_dict[fitbit_id]['data']
            nolab_labels.append(data_dict[fitbit_id]['uniqname'])
    else:
        nolab_data.append(data_dict[fitbit_id]['data'])
        nolab_aggregate += data_dict[fitbit_id]['data']
        nolab_labels.append(fitbit_id)


index = 0
lab_members = ['brghena', 'bradjc', 'ppannuto', 'samkuo', 'mclarkk']
lab_data = []
data_count = 0
lunch_data = []
lunch_count = 0
for uniqname in inlab_labels:
    if uniqname in lab_members:
        print("Sample size for " + uniqname + " = " + str(len(inlab_data[index])))
        data_count += len(inlab_data[index])
        print("Lunch size for " + uniqname + " = " + str(len(inlunch_data[index])))
        lunch_count += len(inlunch_data[index])
        lab_data += inlab_data[index]
        lunch_data += inlunch_data[index]
        #hist = create_hist(inlab_data[index], range(-100, -50))
        #norm = norm_hist(hist)
        #plt.plot(range(-100, -50), norm, '.', label=uniqname, linestyle='-')
        #plt.legend()
    index += 1

print("Data size:", data_count)
print("Lunch size:", lunch_count)

plt.figure(1)
hist = create_hist(lab_data, range(-100, -50))
norm = norm_hist(hist)
plt.plot(range(-100, -50), norm, '.', label='Lab members', linestyle='-')
plt.legend()

plt.figure(2)
hist = create_hist(lunch_data, range(-100, -50))
norm = norm_hist(hist)
plt.plot(range(-100, -50), norm, '.', label='Lab lunch', linestyle='-')
plt.legend()

plt.show()

