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

        if 'uniqname' in loaded_data:
            if 'uniqname' not in data_dict[fitbit_id]:
                data_dict[fitbit_id]['uniqname'] = loaded_data['uniqname']

        data_dict[fitbit_id]['data'].append(loaded_data['rssi'])

lab_members = ['brghena', 'bradjc', 'wwhuang', 'bpkempke', 'sdebruin', 'ppannuto', 'samkuo', 'mclarkk', 'adkinsjd', 'tzachari']

inlab_data = []
inlab_aggregate = []
inlab_labels = []
nolab_data = []
nolab_aggregate = []
nolab_labels = []
for fitbit_id in data_dict:
    if 'uniqname' in data_dict[fitbit_id]:
        if data_dict[fitbit_id]['uniqname'] in lab_members:
            inlab_data.append(data_dict[fitbit_id]['data'])
            inlab_aggregate += data_dict[fitbit_id]['data']
            inlab_labels.append(data_dict[fitbit_id]['uniqname'])
        else:
            nolab_data.append(data_dict[fitbit_id]['data'])
            nolab_aggregate += data_dict[fitbit_id]['data']
            nolab_labels.append(data_dict[fitbit_id]['uniqname'])
    else:
        nolab_data.append(data_dict[fitbit_id]['data'])
        nolab_aggregate += data_dict[fitbit_id]['data']
        nolab_labels.append(fitbit_id)




#plt.figure(1)
#plt.hist(inlab_data, bins=range(-100, -50), range=(-100, -50), stacked=False, histtype='bar', label=inlab_labels)
#plt.legend()

#plt.figure(2)
#plt.hist(nolab_data, range(-100, -40), stacked=False, label=nolab_labels)
#plt.legend()

#plt.figure(3)
#plt.hist([inlab_aggregate, nolab_aggregate], bins=range(-100, -50), range=(-100, -50), stacked=False, histtype='bar', label=['lab member', 'not in lab'])
#plt.legend()

inlab_hist_agg = create_hist(inlab_aggregate, range(-100, -50))
inlab_norm_agg = norm_hist(inlab_hist_agg)
nolab_hist_agg = create_hist(nolab_aggregate, range(-100, -50))
nolab_norm_agg = norm_hist(nolab_hist_agg)

plt.figure(4)
plt.plot(range(-100, -50), inlab_norm_agg, 'g.', label='lab member', fillstyle='bottom', linestyle='-')
plt.plot(range(-100, -50), nolab_norm_agg, 'b.', label='not in lab', fillstyle='full',   linestyle='-')
plt.legend()

#index = 0
#for uniqname in inlab_labels:
#    plt.figure()
#    hist = create_hist(inlab_data[index], range(-100, -50))
#    norm = norm_hist(hist)
#    plt.plot(range(-100, -50), norm, 'b.', label=uniqname, linestyle='-')
#    plt.legend()
#    index += 1

nonlab_members = ['cfwelch', 'evrobert', 'jdejong', 'jhalderm', 'yhguo']
nonlab_data = []
index = 0
plt.figure(5)
for uniqname in nolab_labels:
    if uniqname in nonlab_members:
        print("Sample size for " + uniqname + " = " + str(len(nolab_data[index])))
        nonlab_data += nolab_data[index]
        hist = create_hist(nolab_data[index], range(-100, -50))
        norm = norm_hist(hist)
        plt.plot(range(-100, -50), norm, '.', label=uniqname, linestyle='-')
        plt.legend()
    index += 1

index = 0
plt.figure(6)
lab_members = ['brghena', 'bradjc', 'ppannuto', 'samkuo', 'mclarkk']
lab_data = []
for uniqname in inlab_labels:
    if uniqname in lab_members:
        print("Sample size for " + uniqname + " = " + str(len(inlab_data[index])))
        lab_data += inlab_data[index]
        hist = create_hist(inlab_data[index], range(-100, -50))
        norm = norm_hist(hist)
        plt.plot(range(-100, -50), norm, '.', label=uniqname, linestyle='-')
        plt.legend()
    index += 1

plt.figure(7)
hist = create_hist(nonlab_data, range(-100, -50))
norm = norm_hist(hist)
plt.plot(range(-100, -50), norm, 'b.', label='Non Lab Members', linestyle='-')
plt.axis([-100, -50, 0, 0.16])
plt.legend()
#index = 0
#for val in range(-100, -50):
#    print(str(val) + ": " + str(norm[index]))
#    index += 1

plt.figure(8)
hist = create_hist(lab_data, range(-100, -50))
norm = norm_hist(hist)
plt.plot(range(-100, -50), norm, 'g.', label='Lab Members', linestyle='-')
plt.axis([-100, -50, 0, 0.16])
plt.legend()

plt.figure(9)
hist = create_hist(nonlab_data, range(-100, -50))
norm = norm_hist(hist)
plt.plot(range(-100, -50), norm, 'b.', label='Non Lab Members', linestyle='-')
hist = create_hist(lab_data, range(-100, -50))
norm = norm_hist(hist)
plt.plot(range(-100, -50), norm, 'g.', label='Lab Members', linestyle='-')
plt.axis([-100, -50, 0, 0.16])
plt.legend()

plt.show()

