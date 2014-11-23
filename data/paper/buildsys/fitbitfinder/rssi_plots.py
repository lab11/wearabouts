#!/usr/bin/env python2

# I want to plot rssi values along with labels for each uniqname for 4908 and 4670

import json
import ast
import matplotlib.pyplot as plt

colors = ['b', 'g', 'r', 'c', 'm', 'k']

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

def cdf_make(norm_hist):
    new_cdf = []
    total = 0.0
    for count in norm_hist:
        total += count
        new_cdf.append(total)
    return new_cdf

def choose_color(index):
    return colors[index%len(colors)]

data_dict = {'4908': {}, '4901': {}, '4670': {}}

for loc in data_dict:
    loc_data = data_dict[loc]

    with open(loc + '.data') as f:
        for line in f:
            loaded_data = ast.literal_eval(line)

            if 'rssi' not in loaded_data:
                continue
            if 'uniqname' == 'None':
                continue
            if loaded_data['rssi'] == 0:
                continue
            if loaded_data['rssi'] == 63:
                continue
            if loaded_data['time'] < 1404943278557:
                continue

            fitbit_id = loaded_data['fitbit_id']
            if fitbit_id not in loc_data:
                loc_data[fitbit_id] = {}
                if 'uniqname' in loaded_data:
                    loc_data[fitbit_id]['uniqname'] = loaded_data['uniqname']
                    loc_data[fitbit_id]['full_name'] = loaded_data['full_name']
                else:
                    loc_data[fitbit_id]['uniqname'] = 'unknown'
                    loc_data[fitbit_id]['full_name'] = 'Unknown'

                loc_data[fitbit_id]['rssi'] = []
                loc_data[fitbit_id]['time'] = []
            
            loc_data[fitbit_id]['rssi'].append(loaded_data['rssi'])
            loc_data[fitbit_id]['time'].append(loaded_data['time']/1000.0)

members_4908 = [
        'brghena',
        'bradjc',
        'wwhuang',
        'bpkempke',
        'sdebruin',
        'ppannuto',
        'samkuo',
        'mclarkk',
        'adkinsjd',
        'tzachari',
        'nealjack',
        'immerman',
        'rthaneda',
        'ncnuech',
        'nklugman'
    ]

members_4670 = [
        'micharu'
    ]

for loc in data_dict:
    print(loc + '--')
    for fitbit_id in data_dict[loc]:
        id_data = data_dict[loc][fitbit_id]
        hist = create_hist(id_data['rssi'], range(-100, 0))
        id_data['hist'] = norm_hist(hist)
        id_data['cdf'] = cdf_make(id_data['hist'])
        print(str(id_data['uniqname']) + ' - ' + str(len(id_data['rssi'])))
    print('\n')



# Plot data for 4670
if False:
    plt.figure(1)
    plt.ylabel('Probability of Occurance')
    plt.xlabel('Received Signal Strength Indicator')

    plt.title('BBB 4670')
    loc_data = data_dict['4670']
    index = 1
    for fitbit_id in loc_data:
        id_data = loc_data[fitbit_id]
        
        if (id_data['uniqname'] not in
                ['bradjc', 'ppannuto', 'sdebruin', 'tzachari', 'micharu', 'mclarkk']):
            continue

        plt.subplot(8, 1, index)
        index += 1
        plt.plot(range(-100, 0), id_data['hist'], choose_color(index) + '.',
                label=id_data['uniqname'], fillstyle='bottom', linestyle='-')
        plt.legend()
        plt.axis([-100, 0, 0, 0.30])


if False:
    plt.figure(2)
    plt.ylabel('Probability of Detection')
    plt.xlabel('Received Signal Strength Indicator')

    plt.title('BBB 4670')
    loc_data = data_dict['4670']
    index = 1
    for fitbit_id in loc_data:
        id_data = loc_data[fitbit_id]
        
        if (id_data['uniqname'] not in
                ['bradjc', 'ppannuto', 'sdebruin', 'tzachari', 'micharu', 'mclarkk']):
            continue

        plt.subplot(8, 1, index)
        index += 1
        plt.plot(range(-100, 0), id_data['cdf'], choose_color(index) + '.',
                label=id_data['uniqname'], fillstyle='bottom', linestyle='-')
        plt.plot((-100, 0), (0.5, 0.5), 'y-')
        plt.plot((-100, 0), (0.9, 0.9), 'y-')
        plt.legend()
        plt.axis([-100, 0, 0, 1])

# Plot data for 4908
if False:
    plt.figure(3)
    plt.ylabel('Probability of Occurance')
    plt.xlabel('Received Signal Strength Indicator')

    plt.title('BBB 4908')
    loc_data = data_dict['4908']
    index = 1
    for fitbit_id in loc_data:
        id_data = loc_data[fitbit_id]
        
        if (id_data['uniqname'] not in
                ['bradjc', 'ppannuto', 'sdebruin', 'tzachari', 'micharu', 'mclarkk']):
            continue

        plt.subplot(9, 1, index)
        index += 1
        plt.plot(range(-100, 0), id_data['hist'], choose_color(index) + '.',
                label=id_data['uniqname'], fillstyle='bottom', linestyle='-')
        plt.legend()
        plt.axis([-100, 0, 0, 0.30])


if False:
    plt.figure(4)
    plt.ylabel('Probability of Detection')
    plt.xlabel('Received Signal Strength Indicator')

    plt.title('BBB 4908')
    loc_data = data_dict['4908']
    index = 1
    for fitbit_id in loc_data:
        id_data = loc_data[fitbit_id]
        
        if (id_data['uniqname'] not in
                ['bradjc', 'ppannuto', 'sdebruin', 'tzachari', 'micharu', 'mclarkk']):
            continue

        plt.subplot(9, 1, index)
        index += 1
        plt.plot(range(-100, 0), id_data['cdf'], choose_color(index) + '.',
                label=id_data['uniqname'], fillstyle='bottom', linestyle='-')
        plt.plot((-100, 0), (0.5, 0.5), 'y-')
        plt.plot((-100, 0), (0.9, 0.9), 'y-')
        plt.legend()
        plt.axis([-100, 0, 0, 1])


# Plot data for a given fitbit_idess from across all rooms
if True:
    target_fitbit_ids = {
        '27E78B1E97F9': 'brghena',
        '4D8D0D8CB7EE': 'bradjc',
        'C372A4DA26C4': 'samkuo',
        '6033E07D95F9': 'ppannuto'
        }

    for fitbit_id in target_fitbit_ids:
        f, axarr = plt.subplots(2, sharex=True)
        axarr[0].set_title(target_fitbit_ids[fitbit_id] + ' (' + str(fitbit_id) + ')')

        axarr[1].set_ylabel('Probability of Detection')
        axarr[1].set_xlabel('Received Signal Strength Indicator')

        index = 0
        for loc in data_dict:
            if loc == '4901':
                continue
            
            if fitbit_id not in data_dict[loc]:
                print(target_fitbit_ids[fitbit_id] + " not in " + loc)
                #exit()
                continue

            id_data = data_dict[loc][fitbit_id]

            label_str = loc + ' - ' + str(len(id_data['rssi'])) + " samples"
            axarr[0].plot(range(-100, 0), id_data['hist'], choose_color(index) + '.',
                    label=label_str, fillstyle='bottom', linestyle='-')
            axarr[0].legend()
            axarr[0].set_xbound(-100, 0)
            axarr[0].set_ybound(0, 0.30)

            axarr[1].plot(range(-100, 0), id_data['cdf'], choose_color(index) + '.',
                    label=label_str, fillstyle='bottom', linestyle='-')
            axarr[1].legend()
            axarr[1].set_xbound(-100, 0)
            axarr[1].set_ybound(0, 1)
            index += 1


# Plot RSSI over sample count for a given fitbit_idess across all rooms
if False:
    target_fitbit_ids = {
        '27E78B1E97F9': 'brghena',
        '4D8D0D8CB7EE': 'bradjc',
        'C372A4DA26C4': 'samkuo',
        '6033E07D95F9': 'ppannuto'
        }

    for fitbit_id in target_fitbit_ids:
        f, axarr = plt.subplots(3, sharex=True)
        axarr[0].set_title(target_fitbit_ids[fitbit_id] + ' (' + str(fitbit_id) + ')')

        axarr[2].set_ylabel('RSSI')
        axarr[2].set_xlabel('Sample Number')

        index = 0
        max_len = 0
        for loc in data_dict:

            if fitbit_id not in data_dict[loc]:
                print(target_fitbit_ids[fitbit_id] + " not in " + loc)
                exit()

            id_data = data_dict[loc][fitbit_id]

            samples = len(id_data['rssi'])
            if samples > max_len:
                max_len = samples

            label_str = loc + ' - ' + str(samples) + " samples"
            axarr[index].plot(range(0, samples), id_data['rssi'],
                    choose_color(index) + '.', label=label_str, fillstyle='bottom', linestyle='-')
            axarr[index].legend()
            axarr[index].set_ybound(-100, 0)
            index += 1

        axarr[2].set_xbound(0, max_len)


# Plot RSSI over time for a given fitbit_idess across all rooms
if True:
    target_fitbit_ids = {
        '27E78B1E97F9': 'brghena',
        '4D8D0D8CB7EE': 'bradjc',
        'C372A4DA26C4': 'samkuo',
        '6033E07D95F9': 'ppannuto'
        }

    for fitbit_id in target_fitbit_ids:
        f, axarr = plt.subplots(1, sharex=True)
        axarr.set_title(target_fitbit_ids[fitbit_id] + ' (' + str(fitbit_id) + ')')

        axarr.set_ylabel('RSSI')
        axarr.set_xlabel('Sample Number')

        times = []
        for loc in data_dict:
            if loc == '4901':
                continue

            if fitbit_id not in data_dict[loc]:
                print(target_fitbit_ids[fitbit_id] + " not in " + loc)
                #exit()
                continue

            id_data = data_dict[loc][fitbit_id]

            samples = len(id_data['rssi'])

            label_str = loc + ' - ' + str(samples) + " samples"
            axarr.plot(id_data['time'], id_data['rssi'],
                    '.', label=label_str, fillstyle='bottom', linestyle='-')
            axarr.legend()
            axarr.set_ybound(-100, 0)
            times.append(id_data['time'][0])
            times.append(id_data['time'][-1])
            #print("Running from: " + str(id_data['time'][0]) + " to " + str(id_data['time'][-1]))

        axarr.set_xbound(min(times), max(times))


# Plot in-lab vs out-of-lab aggregates
if True:
    # create aggregates
    inlab_agg = []
    outlab_agg = []

    loc_data = data_dict['4908']
    for fitbit_id in loc_data:
        if loc_data[fitbit_id]['uniqname'] in members_4908:
            inlab_agg += loc_data[fitbit_id]['rssi']
            print(loc_data[fitbit_id]['uniqname'] + " in lab")
        else:
            if loc_data[fitbit_id]['uniqname'] != 'davadria':
                outlab_agg += loc_data[fitbit_id]['rssi']
                print(loc_data[fitbit_id]['uniqname'] + " not in lab")

    # create normalized histograms of them
    inlab_hist = norm_hist(create_hist(inlab_agg, range(-100, 0)))
    outlab_hist = norm_hist(create_hist(outlab_agg, range(-100, 0)))
    inlab_cdf = cdf_make(inlab_hist)
    outlab_cdf = cdf_make(outlab_hist)

    # plot
    f, axarr = plt.subplots(2, sharex=True)
    axarr[0].set_title('BBB 4908')

    axarr[1].set_ylabel('Probability of Occurence')
    axarr[1].set_xlabel('Received Signal Strength Indicator')

    axarr[0].plot(range(-100, 0), inlab_hist, choose_color(0) + '.',
            label='4908 Lab Members', fillstyle='bottom', linestyle='-')
    axarr[0].plot(range(-100, 0), outlab_hist, choose_color(1) + '.',
            label='Other Building Occupants', fillstyle='bottom', linestyle='-')
    axarr[0].legend()
    axarr[0].set_ybound(0, 0.20)

    axarr[1].plot(range(-100, 0), inlab_cdf, choose_color(0) + '.',
            label='4908 Lab Members', fillstyle='bottom', linestyle='-')
    axarr[1].plot(range(-100, 0), outlab_cdf, choose_color(1) + '.',
            label='Other Building Occupants', fillstyle='bottom', linestyle='-')
    axarr[1].plot((-100, 0), (0.5, 0.5), 'y-')
    axarr[1].plot((-100, 0), (0.9, 0.9), 'y-')
    axarr[1].legend()
    axarr[1].set_ybound(0, 1)

    axarr[1].set_xbound(-100, 0)



# Show plots!
plt.show()

