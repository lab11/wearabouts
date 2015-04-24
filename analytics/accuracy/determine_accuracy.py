#!/usr/bin/env python

# Records presence as if only 4908 has a scanner
#   with present meaning any packet seen in the last minute
#   with absent meaning no packet seen in the last minute

import time
import operator
import dataprint

people = ['sarparis', 'samkuo', 'nealjack', 'adkinsjd', 'brghena', 'bpkempke']

transitions = dict(zip(people,[{}, {}, {}, {}, {}, {}]))

# parse all presence changes in ground truth
gt_file = open('ground_truth_parsed.dat', 'r')
prev_state = dict(zip(people,[-1]*6))
for line in gt_file:
    if line[0] == '#':
        continue

    time = float(line.split()[1])
    data = dict(zip(people,[int(x) for x in line.split()[2:]]))

    # looking for state changes only
    if data == prev_state:
        continue

    for person in data:
        if prev_state[person] != data[person]:
            transitions[person][time] = ('gt', prev_state[person], data[person])

    prev_state = data


# parse all presence changes in wearabouts
wb_file = open('rssi_data_4908only_seen.dat', 'r')
prev_state = dict(zip(people,[-1]*6))
for line in wb_file:
    if line[0] == '#':
        continue

    time = float(line.split()[1])
    data = dict(zip(people,[int(x) for x in line.split()[2:]]))

    # looking for state changes only
    if data == prev_state:
        continue

    for person in data:
        if prev_state[person] != data[person]:
            transitions[person][time] = ('wb', prev_state[person], data[person])

    prev_state = data


#print(transitions['samkuo'])

# iterate through changes for each person, determining accuracy
#   time starts at 10:30:00 AM with everyone absent
stats = {}
#for person in ['samkuo']:
for person in people:
    
    wb_prev_data = -1
    gt_prev_data = -1
    prev_transition = ''
    missed_events = 0
    false_events = 0
    entry_latency = []
    exit_latency = []
    
    prev_time = -1973.0
    match_time = 0.0
    diff_time = 0.0
    total_time = 0.0
    lab_time = 0.0
    none_time = 0.0

    #print('\n\nPerson: ' + str(person))

    for timestamp in sorted(transitions[person].keys()):

        # add the last period to matching time or different time
        #print(str(prev_time) + ': ' + str(gt_prev_data) + ' ' + str(wb_prev_data))
        if wb_prev_data == gt_prev_data:
            match_time += timestamp-prev_time
            #print("match until: " + str(timestamp))
        else:
            diff_time += timestamp-prev_time
            #print("diff until: " + str(timestamp))

        total_time += timestamp-prev_time

        if gt_prev_data == 0:
            #print("past time in lab")
            lab_time += timestamp-prev_time
        elif gt_prev_data == -1:
            #print("past time nowhere")
            none_time += timestamp-prev_time

        if False:
            if prev_transition == 'gt':
                if transitions[person][timestamp][0] == 'gt':
                    missed_events += 1
                else:
                    #if 
                        # entry or exit
                        pass

            else:
                if transitions[person][timestamp][0] == 'wb':
                    false_events += 1
                else:
                    # entry or exit
                    pass

        prev_time = timestamp
        #print(str(timestamp) + ' ' + str(transitions[person][timestamp]))
        if transitions[person][timestamp][0] == 'gt':
            #print("gt previous -> " + str(transitions[person][timestamp][2]))
            gt_prev_data = transitions[person][timestamp][2]
        else:
            #print("wb previous -> " + str(transitions[person][timestamp][2]))
            wb_prev_data = transitions[person][timestamp][2]

        #print('')

    # loop over, add remaining data
    timestamp = 43216.0
    if wb_prev_data == gt_prev_data:
        match_time += timestamp-prev_time
        #print("match until: " + str(timestamp))
    else:
        diff_time += timestamp-prev_time
        #print("diff until: " + str(timestamp))
    total_time += timestamp-prev_time
    if gt_prev_data == 0:
        #print("past time in lab")
        lab_time += timestamp-prev_time
    elif gt_prev_data == -1:
        #print("past time nowhere")
        none_time += timestamp-prev_time

    stats[person] = [match_time, diff_time, total_time, lab_time, none_time]


total_time = 43216.0 + 1973.0
accuracy_list = []
out_data = [['#uniqname', 'match_time', 'diff_time', '% in lab', '% not in lab', 'accuracy']]
for person in ['sarparis', 'samkuo', 'adkinsjd', 'brghena']:
    match_time = stats[person][0]
    diff_time = stats[person][1]
    total_time = stats[person][2]
    lab_time = stats[person][3]
    none_time = stats[person][4]
    data = [match_time, diff_time, lab_time/total_time, none_time/total_time, match_time/total_time]
    accuracy_list.append(match_time/total_time)

    out_data.append([person]+data)
    #print(str(person) + '\t' +
    #        str(match_time) + '\t' + str(diff_time) + '\t'+
    #        str(float(match_time)/(match_time+diff_time)) + '\t' +
    #        #str(match_time/total_time) + '\t' + 
    #        #str(total_time) + '\t' + 
    #        #str(lab_time) + '\t' +
    #        str(lab_time/total_time) + '\t' +
    #        #str(none_time) + '\t' +
    #        str(none_time/total_time))

dataprint.to_newfile('accuracy.stats', out_data, overwrite=True)
print("Complete")
print("Avg accuracy: " + str(sum(accuracy_list)/len(accuracy_list)))

