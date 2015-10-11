#!/usr/bin/env python

import dataprint
import time

#ground_truths = [('../camera/camera_minimized.dat', [0]), ('../rfid/rfid_minimized.dat', [0,1,2]), ('../amalgamated_truth/first_amalgamated_dataset.dat', [0,1,2])]
ground_truths = [('../amalgamated_truth/first_amalgamated_dataset.dat', [0])]
wearabouts_file = '../wearabouts/wearabouts_minimized.dat'

users = {'samkuo': 2, 'brghena': 3, 'azhen': 4, 'bradjc': 5, 'sdebruin': 8, 'sairohit': 14}
user_data = {}

# 72 hours total
start_time = 1937 # Day 1, 19:00
end_time = 261137 # Day 4, 19:00

for ground_truth_data in ground_truths:
    ground_truth_file = ground_truth_data[0]
    ground_truth_locs = ground_truth_data[1]

    true_file = open(ground_truth_file, 'r')
    true_data = [line.split() for line in true_file]
    true_file.close()

    test_file = open(wearabouts_file, 'r')
    test_data = [line.split() for line in test_file]
    test_file.close()

    # create time-based dataset
    time_data = {}
    for data in true_data[1:]:
        # skip comments
        if data[0] == '#':
            continue

        timestamp = float(data[1])
        if timestamp in time_data:
            print("Overlap: " + str(data))
            exit()

        # add new data element
        #   mark which dataset its from, add filler to make offsets for data correct
        #   add state data
        time_data[timestamp] = ["true", 0] + data[2:]
    for data in test_data[1:]:
        # skip comments
        if data[0] == '#':
            continue

        timestamp = float(data[1])
        if timestamp in time_data:
            print("Overlap: " + str(data))
            exit()

        # add new data element
        #   mark which dataset its from, add filler to make offsets for data correct
        #   add state data
        time_data[timestamp] = ["test", 0] + data[2:]
    # keep a sorted list of the times to iterate through
    time_keys = sorted(time_data.keys())

    tiny_offset = 0.0

    for user in users:
        print("On user: " + str(user))

        error_data = []
        error_data.append(['#time', 'seconds', str(user)])
        error_state = 0
        prev_error_state = None

        # setup
        time_index = 0
        curr_time = time_keys[time_index]
        user_index = users[user]
        true_state = -1
        test_state = -1
        if user not in user_data:
            user_data[user] = {}
        user_data[user][ground_truth_file] = {
                'total_time':           0,
                'time_tracked':         0,
                'time_not_found':       0,
                'true_positive':        0,
                'false_positive':       0,
                'true_negative':        0,
                'false_negative':       0,
                }
        stats = user_data[user][ground_truth_file]
        mismatches = [[],[]]

        # strategy:
        # start, known state at start time
        # get next time data
        #   (next_time - curr_time) goes to category based on currteststate and currtruestate
        #   update appropriate state (true or test)
        #   advance time to next_time
        # keep going until next_time > end time
        #   (end_time - curr_time) goes to category

        # iterate until we get to the start time, keeping track of state
        while curr_time < start_time:
            # update states to new state at current time
            if time_data[curr_time][0] == 'true':
                true_state = int(time_data[curr_time][user_index])
            else:
                test_state = int(time_data[curr_time][user_index])

            # grab next timestamp
            time_index += 1
            curr_time = time_keys[time_index]

        # track stats from start_time until curr_time
        prev_time = start_time
        # time tracking
        stats['total_time'] += curr_time-prev_time
        if true_state in ground_truth_locs:
            # in ground_truth_room
            stats['time_tracked'] += curr_time-prev_time
        elif true_state == -1:
            # not found
            stats['time_not_found'] += curr_time-prev_time
        # accuracy tracking
        if true_state in ground_truth_locs:
            # in tracked room
            if test_state == true_state:
                stats['true_positive'] += curr_time-prev_time
                error_state = 0
            else:
                stats['false_negative'] += curr_time-prev_time
                mismatches[0].append(curr_time-prev_time)
                error_state = -1
        else:
            # not in tracked room, possibly not found
            if test_state in ground_truth_locs:
                stats['false_positive'] += curr_time-prev_time
                mismatches[1].append(curr_time-prev_time)
                error_state = 1
            else:
                # neither true nor test in a tracked location
                #   only count this data if they are both in "unknown"
                #   wearabouts guess as another random room shouldn't true negative or false positive
                error_state = 0
                if test_state == -1 and true_state == -1:
                    stats['true_negative'] += curr_time-prev_time
        # append error_data
        if error_state != prev_error_state:
            # need a small offset here so that everyone doesn't overlap
            tiny_offset += 0.000001
            time_list = [time.strftime('%H:%M:%S', time.localtime(prev_time)), prev_time+tiny_offset]
            error_data.append(time_list+[error_state])
        prev_error_state = error_state

        # track state until next_time > end_time, mark category for each time period
        while True:
            # update states to new state at current time
            if time_data[curr_time][0] == 'true':
                true_state = int(time_data[curr_time][user_index])
            else:
                test_state = int(time_data[curr_time][user_index])

            # grab next timestamp
            prev_time = curr_time
            time_index += 1
            curr_time = time_keys[time_index]
            if curr_time > end_time:
                break

            # track stats for time period
            # time tracking
            stats['total_time'] += curr_time-prev_time
            if true_state in ground_truth_locs:
                # in ground_truth_room
                stats['time_tracked'] += curr_time-prev_time
            elif true_state == -1:
                # not found
                stats['time_not_found'] += curr_time-prev_time
            # accuracy tracking
            if true_state in ground_truth_locs:
                # in tracked room
                if test_state == true_state:
                    stats['true_positive'] += curr_time-prev_time
                    error_state = 0
                else:
                    stats['false_negative'] += curr_time-prev_time
                    mismatches[0].append(curr_time-prev_time)
                    error_state = -1
            else:
                # not in tracked room, possibly not found
                if test_state in ground_truth_locs:
                    stats['false_positive'] += curr_time-prev_time
                    mismatches[1].append(curr_time-prev_time)
                    error_state = 1
                else:
                    # neither true nor test in a tracked location
                    #   only count this data if they are both in "unknown"
                    #   wearabouts guess as another random room shouldn't true negative or false positive
                    error_state = 0
                    if test_state == -1 and true_state == -1:
                        stats['true_negative'] += curr_time-prev_time
            # append error_data
            if error_state != prev_error_state:
                time_list = [time.strftime('%H:%M:%S', time.localtime(prev_time)), prev_time]
                error_data.append(time_list+[error_state])
            prev_error_state = error_state

        # track stats from prev_time until end_time
        curr_time = end_time
        # time tracking
        stats['total_time'] += curr_time-prev_time
        if true_state in ground_truth_locs:
            # in ground_truth_room
            stats['time_tracked'] += curr_time-prev_time
        elif true_state == -1:
            # not found
            stats['time_not_found'] += curr_time-prev_time
        # accuracy tracking
        if true_state in ground_truth_locs:
            # in tracked room
            if test_state == true_state:
                stats['true_positive'] += curr_time-prev_time
                error_state = 0
            else:
                stats['false_negative'] += curr_time-prev_time
                mismatches[0].append(curr_time-prev_time)
                error_state = -1
        else:
            # not in tracked room, possibly not found
            if test_state in ground_truth_locs:
                stats['false_positive'] += curr_time-prev_time
                mismatches[1].append(curr_time-prev_time)
                error_state = 1
            else:
                # neither true nor test in a tracked location
                #   only count this data if they are both in "unknown"
                #   wearabouts guess as another random room shouldn't true negative or false positive
                error_state = 0
                if test_state == -1 and true_state == -1:
                    stats['true_negative'] += curr_time-prev_time
        # append error_data
        if error_state != prev_error_state:
            time_list = [time.strftime('%H:%M:%S', time.localtime(prev_time)), prev_time]
            error_data.append(time_list+[error_state])
        prev_error_state = error_state

        # finished with user
        error_file = open('results/' + user + '_errors.dat', 'w')
        dataprint.to_file(error_file, error_data)
        error_file.close()

        ## print stats
        #tp = stats['true_positive']
        #fp = stats['false_positive']
        #tn = stats['true_negative']
        #fn = stats['false_negative']
        #print("Stats: ")
        #print("\taccuracy  = " + str((tp+tn)/(tp+fp+fn+tn)))
        #try:
        #    print("\tprecision = " + str((tp)/(tp+fp)))
        #except ZeroDivisionError:
        #    print("\tprecision = broken")
        #try:
        #    print("\trecall    = " + str((tp)/(tp+fn)))
        #except ZeroDivisionError:
        #    print("\tprecision = broken")
        #
        ## output file of error events
        #out_data = []
        #out_data.append(['#false negative', 'false positive'])
        #for index in range(max(len(mismatches[0]), len(mismatches[1]))):
        #    if index < len(mismatches[0]) and index < len(mismatches[1]):
        #        out_data.append([mismatches[0][index], mismatches[1][index]])
        #    elif index < len(mismatches[0]):
        #        out_data.append([mismatches[0][index], ''])
        #    elif index < len(mismatches[1]):
        #        out_data.append(['', mismatches[1][index]])
        #    else:
        #        print("I did something wrong")
        #        exit()
        #event_file = open(user+'_falseEvents.dat', 'w')
        #dataprint.to_file(event_file, out_data)
        #event_file.close()

    # finished with file
    print('\n\n')

print("Complete!\n")
print(user_data)


