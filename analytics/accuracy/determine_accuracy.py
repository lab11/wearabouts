#!/usr/bin/env python

# Records presence as if only 4908 has a scanner
#   with present meaning any packet seen in the last minute
#   with absent meaning no packet seen in the last minute

import sys
import time
import operator
import dataprint

label = ''
if len(sys.argv) == 2:
    label = sys.argv[1]

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
in_filename = 'wb_rssi_data.dat'
if len(sys.argv) >= 2:
    in_filename = sys.argv[1]
wb_file = open(in_filename, 'r')
#wb_file = open('rssi_data_4908only_seen.dat', 'r')
#wb_file = open('rssi_data_allRooms_seen.dat', 'r')
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

# locations actually monitored by ground truth
#   wearabouts data indicating a location other than these locations
#   while ground truth is -1, are true negatives (it has accurately decided we
#   are not in a monitored location)
gt_locations = [0]

#print(transitions['samkuo'])

# iterate through changes for each person, determining accuracy
#   time starts at 10:30:00 AM with everyone absent
stats = {}
#for person in ['samkuo']:
for person in people:
    
    wb_prev_data = -1
    gt_prev_data = -1

    prev_time = -1973.0
    match_time = 0.0
    diff_time = 0.0
    total_time = 0.0
    #lab_time = 0.0
    #absent_time = 0.0

    match_lab_time = 0.0
    match_absent_time = 0.0
    diff_wb_lab_time = 0.0
    diff_wb_absent_time = 0.0

    missed_events = 0
    missed_event_durations = []
    false_events = 0
    false_event_durations = []
    gt_event_start = 0
    wb_event_start = 0
    gt_event_detected = True
    wb_event_valid = True
    entry_latencies = []
    exit_latencies = []

    #print('\n\nPerson: ' + str(person))

    for timestamp in sorted(transitions[person].keys()):

        # record the time for the last period into proper bins
        total_time += timestamp-prev_time
        if wb_prev_data == gt_prev_data:
            match_time += timestamp-prev_time
            if wb_prev_data in gt_locations:
                # true positive
                match_lab_time += timestamp-prev_time
            else:
                # true negative
                match_absent_time += timestamp-prev_time
        else:
            if gt_prev_data == -1 and wb_prev_data not in gt_locations:
                # wearabouts guesses we are in another room, when we are ground truth not in lab
                match_time += timestamp-prev_time
                match_absent_time += timestamp-prev_time
            else:
                if gt_prev_data not in gt_locations and wb_prev_data not in gt_locations:
                    # safety assertion
                    print("ERROR")
                    exit(1)

                diff_time += timestamp-prev_time
                if wb_prev_data in gt_locations:
                    # false negative
                    diff_wb_lab_time += timestamp-prev_time
                else:
                    # false positive
                    diff_wb_absent_time += timestamp-prev_time
        #if gt_prev_data == 0:
        #    lab_time += timestamp-prev_time
        #else:
        #    absent_time += timestamp-prev_time

        # determine latency
        if transitions[person][timestamp][0] == 'gt':
            # ground truth data
            curr_data = transitions[person][timestamp][2]

            if curr_data == gt_prev_data:
                # event continues
                pass
            else:
                # event has changed. We are somewhere new

                # handle end of old event
                if not gt_event_detected:
                    # the previous event was missed by wearabouts
                    #print(str(person) + " has missed event at " + str(timestamp) + '  gt goes from ' + str(gt_prev_data) + ' to ' + str(curr_data))
                    missed_events += 1
                    missed_event_durations.append(timestamp-gt_event_start)

                # handle start of new event
                gt_event_start = timestamp
                if curr_data != wb_prev_data:
                    # wearabouts disagrees with us
                    if curr_data in gt_locations or wb_prev_data in gt_locations:
                        # wearabouts is actually wrong. This is either a late
                        #   detection or a false event
                        gt_event_detected = False
                    else:
                        # ground truth unknown and wearabouts put us in an untracked room. Counts as a match
                        gt_event_detected = True
                        wb_event_valid = True
                        exit_latencies.append(wb_event_start-timestamp) #latency is negative
                elif curr_data == wb_prev_data:
                    if not wb_event_valid:
                        # wearabouts already agrees with us!
                        gt_event_detected = True
                        wb_event_valid = True
                        if curr_data in gt_locations:
                            entry_latencies.append(wb_event_start-timestamp) # latency is negative
                        else:
                            exit_latencies.append(wb_event_start-timestamp) # latency is negative
                    else:
                        # ground truth returning after a missed event
                        gt_event_detected = True
                else:
                    # invalid state
                    print("Invalid 1")
                    exit(1)

        else:
            # wearabouts data
            curr_data = transitions[person][timestamp][2]

            if (curr_data == wb_prev_data or
                    (wb_prev_data not in gt_locations and curr_data not in gt_locations)):
                # event continues or non-event continues
                pass
            else:
                # event has changed. Wearabouts thinks we are somewhere new

                # handle end of old event
                if not wb_event_valid:
                    # the previous event was a false one
                    #print(str(person) + " has false event at " + str(timestamp) + '  wb goes from ' + str(wb_prev_data) + ' to ' + str(curr_data))
                    false_events += 1
                    false_event_durations.append(timestamp-wb_event_start)

                # handle start of new event
                wb_event_start = timestamp
                if curr_data != gt_prev_data:
                    # we disagree from ground truth. Good job
                    if gt_prev_data in gt_locations or curr_data in gt_locations:
                        # wearabouts thinks something changed. This is either
                        #   a false event or an early detection
                        wb_event_valid = False
                    else:
                        # wearabouts in untracked room
                        if not gt_event_detected:
                            # ground truth unknown and wearabouts untracked 
                            gt_event_detected = True
                            wb_event_valid = True
                            exit_latencies.append(timestamp-gt_event_start) # latency is positive
                        else:
                            # wearabouts had a false event with ground truth unknown
                            wb_event_valid = True
                elif curr_data == gt_prev_data:
                    if not gt_event_detected:
                        # we finally detected a ground truth change
                        wb_event_valid = True
                        gt_event_detected = True
                        if curr_data in gt_locations:
                            entry_latencies.append(timestamp-gt_event_start) # latency is positive
                        else:
                            exit_latencies.append(timestamp-gt_event_start) # latency is positive
                    else:
                        # returning to valid after a false event
                        wb_event_valid = True
                else:
                    # invalid state
                    print("Invalid 2")
                    exit(1)
        #print(str(wb_prev_data) + ' ' + str(gt_prev_data) + ' ' + str(transitions[person][timestamp][0]) + ' ' + str(curr_data) + ' ' + str(wb_event_valid) + ' ' + str(gt_event_detected))
        
        # update data
        prev_time = timestamp
        if transitions[person][timestamp][0] == 'gt':
            gt_prev_data = transitions[person][timestamp][2]
        else:
            wb_prev_data = transitions[person][timestamp][2]


    # loop over, add remaining data
    timestamp = 43216.0
    total_time += timestamp-prev_time
    if wb_prev_data == gt_prev_data:
        match_time += timestamp-prev_time
        if wb_prev_data in gt_locations:
            # true positive
            match_lab_time += timestamp-prev_time
        else:
            # true negative
            match_absent_time += timestamp-prev_time
    else:
        if gt_prev_data == -1 and wb_prev_data not in gt_locations:
            # wearabouts guesses we are in another room, when we are ground truth not in lab
            match_time += timestamp-prev_time
            match_absent_time += timestamp-prev_time
        else:
            if gt_prev_data not in gt_locations and wb_prev_data not in gt_locations:
                # safety assertion
                print("ERROR")
                exit(1)

            diff_time += timestamp-prev_time
            if wb_prev_data in gt_locations:
                # false negative
                diff_wb_lab_time += timestamp-prev_time
            else:
                # false positive
                diff_wb_absent_time += timestamp-prev_time

    # no more events occur, so no latencies or false/missed events to record

    # report data
    avg_missed_duration = 0
    if len(missed_event_durations) > 0:
        avg_missed_duration = sum(missed_event_durations)/len(missed_event_durations)
    avg_false_duration = 0
    if len(false_event_durations) > 0:
        avg_false_duration = sum(false_event_durations)/len(false_event_durations)
    avg_entry_latency = 0
    if len(entry_latencies) > 0:
        avg_entry_latency = sum(entry_latencies)/len(entry_latencies)
    avg_exit_latency = 0
    if len(exit_latencies) > 0:
        avg_exit_latency = sum(exit_latencies)/len(exit_latencies)
    stats[person] = [match_time, diff_time, total_time,
            match_lab_time, match_absent_time, diff_wb_lab_time, diff_wb_absent_time,
            missed_events, avg_missed_duration, false_events, avg_false_duration,
            avg_entry_latency, avg_exit_latency]


total_time = 43216.0 + 1973.0 # = 45189
missed_list = []
missed_duration_list = []
false_list = []
false_duration_list = []
entry_latency_list = []
exit_latency_list = []
accuracy_list = []
precision_list = []
recall_list = []
out_data = []
#out_data = [['#label', 'uniqname', 'match_time', 'diff_time', 'accuracy',
#        'true positive', 'true negative', 'false positive', 'false negative',
#        'precision', 'recall', 'false positive rate']]
for person in ['sarparis', 'samkuo', 'adkinsjd', 'brghena']:
    (match_time, diff_time, total_time,
            match_lab_time, match_absent_time, diff_wb_lab_time, diff_wb_absent_time,
            missed_events, avg_missed_duration, false_events, avg_false_duration,
            avg_entry_latency, avg_exit_latency) = stats[person]

    accuracy = match_time/total_time
    precision = match_lab_time/(match_lab_time+diff_wb_lab_time)
    recall = match_lab_time/(match_lab_time+diff_wb_absent_time)
    false_positive_rate = diff_wb_lab_time/(diff_wb_lab_time+match_absent_time)
    accuracy_list.append(accuracy)
    precision_list.append(precision)
    recall_list.append(recall)
    missed_list.append(missed_events)
    missed_duration_list.append(avg_missed_duration)
    false_list.append(false_events)
    false_duration_list.append(avg_false_duration)
    entry_latency_list.append(avg_entry_latency)
    exit_latency_list.append(avg_exit_latency)

    data = [match_time, diff_time, accuracy,
        match_lab_time, match_absent_time, diff_wb_lab_time, diff_wb_absent_time,
        precision, recall, false_positive_rate,
        missed_events, avg_missed_duration, false_events, avg_false_duration,
        avg_entry_latency, avg_exit_latency]

    out_data.append([label, person]+data)
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
print("False events: " + str(sum(false_list)))
#print(str(false_duration_list))
print("Avg false event duration : " + str(sum(false_duration_list)/len(false_duration_list)))
print("Missed events: " + str(sum(missed_list)))
#print(str(missed_duration_list))
print("Avg missed event duration : " + str(sum(missed_duration_list)/len(missed_duration_list)))
print("")
print("Avg entry latency: " + str(sum(entry_latency_list)/len(entry_latency_list)))
print("Avg exit latency: " + str(sum(exit_latency_list)/len(exit_latency_list)))
print("")
print("Avg accuracy:  " + str(sum(accuracy_list)/len(accuracy_list)))
print("Avg precision: " + str(sum(precision_list)/len(precision_list)))
print("Avg recall:    " + str(sum(recall_list)/len(recall_list)))

