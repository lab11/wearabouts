#!/usr/bin/env python

# steps:
#X  run wearabouts on each person with given BLE_DURATION and BLE_MINIMUM_COUNT
#X  combine files from individuals into a single file equivalent to real wearabouts files
#       (compare against real file to ensure this is working...)
#X  run accuracy comparison on wearabouts results vs amalgamated data

import dataprint
import sys

#ground_truths = [('../camera/camera_minimized.dat', [0]), ('../rfid/rfid_minimized.dat', [0,1,2]), ('../amalgamated_truth/first_amalgamated_dataset.dat', [0,1,2])]
ground_truths = [('../amalgamated_truth/first_amalgamated_dataset.dat', [0,1,2])]
wearabouts_file = 'results/assembled_dataset.dat'

users = {'samkuo': 2, 'brghena': 3, 'azhen': 4, 'bradjc': 5, 'sdebruin': 8, 'sairohit': 14}
user_data = {}

out_data = []
if len(sys.argv) == 3:
    BLE_DURATION = sys.argv[1]
    BLE_MINIMUM_COUNT = sys.argv[2]
else:
    print("ERROR. I demand input arguments!!\n\tBLE_DURATION\tBLE_MINIMUM_COUNT")
    exit()
out_data.append(BLE_DURATION)
out_data.append(BLE_MINIMUM_COUNT)

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

        time = float(data[1])
        if time in time_data:
            print("Overlap: " + str(data))
            exit()

        # add new data element
        #   mark which dataset its from, add filler to make offsets for data correct
        #   add state data
        time_data[time] = ["true", 0] + data[2:]
    for data in test_data[1:]:
        # skip comments
        if data[0] == '#':
            continue

        time = float(data[1])
        if time in time_data:
            print("Overlap: " + str(data))
            exit()

        # add new data element
        #   mark which dataset its from, add filler to make offsets for data correct
        #   add state data
        time_data[time] = ["test", 0] + data[2:]
    # keep a sorted list of the times to iterate through
    time_keys = sorted(time_data.keys())

    for user in users:
        print("On user: " + str(user))

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
            else:
                stats['false_negative'] += curr_time-prev_time
                mismatches[0].append(curr_time-prev_time)
        else:
            # not in tracked room, possibly not found
            if test_state in ground_truth_locs:
                stats['false_positive'] += curr_time-prev_time
                mismatches[1].append(curr_time-prev_time)
            else:
                # neither true nor test in a tracked location
                #   only count this data if they are both in "unknown"
                #   wearabouts guess as another random room shouldn't true negative or false positive
                if test_state == -1 and true_state == -1:
                    stats['true_negative'] += curr_time-prev_time

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
                else:
                    stats['false_negative'] += curr_time-prev_time
                    mismatches[0].append(curr_time-prev_time)
            else:
                # not in tracked room, possibly not found
                if test_state in ground_truth_locs:
                    stats['false_positive'] += curr_time-prev_time
                    mismatches[1].append(curr_time-prev_time)
                else:
                    # neither true nor test in a tracked location
                    #   only count this data if they are both in "unknown"
                    #   wearabouts guess as another random room shouldn't true negative or false positive
                    if test_state == -1 and true_state == -1:
                        stats['true_negative'] += curr_time-prev_time

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
            else:
                stats['false_negative'] += curr_time-prev_time
                mismatches[0].append(curr_time-prev_time)
        else:
            # not in tracked room, possibly not found
            if test_state in ground_truth_locs:
                stats['false_positive'] += curr_time-prev_time
                mismatches[1].append(curr_time-prev_time)
            else:
                # neither true nor test in a tracked location
                #   only count this data if they are both in "unknown"
                #   wearabouts guess as another random room shouldn't true negative or false positive
                if test_state == -1 and true_state == -1:
                    stats['true_negative'] += curr_time-prev_time

        # finished with user
        # print stats
        tp = stats['true_positive']
        fp = stats['false_positive']
        tn = stats['true_negative']
        fn = stats['false_negative']
        print("Stats: ")
        accuracy = (tp+tn)/(tp+fp+fn+tn)
        print("\taccuracy  = " + str(accuracy))
        precision = 0
        try:
            precision = (tp)/(tp+fp)
            print("\tprecision = " + str(precision))
        except ZeroDivisionError:
            print("\tprecision = broken")
        recall = 0
        try:
            recall = (tp)/(tp+fn)
            print("\trecall    = " + str(recall))
        except ZeroDivisionError:
            print("\trecall    = broken")
        fp_rate = 1
        try:
            fp_rate = (fp)/(fp+tn)
            print("\tfp rate  = " + str(fp_rate))
        except ZeroDivisionError:
            print("\tfp rate  = broken")

        # keep a list of data for each user
        # duration, min_count, [tp, fp, tn, fn, acc, pre, rec, num_fp, num_fp<60, num_fn, num_fn<60]*users
        out_data += [tp, fp, tn, fn, accuracy, precision, recall, fp_rate]
        num_fp = len(mismatches[1])
        num_fp_lt60 = len([x for x in mismatches[1] if x < 60])
        num_fn = len(mismatches[0])
        num_fn_lt60 = len([x for x in mismatches[0] if x < 60])
        out_data += [num_fp, num_fp_lt60, num_fn, num_fn_lt60]

    # finished with file
    print('\n\n')

outfile = open('results/stats.csv', 'a+')
outfile.write(','.join([str(x) for x in out_data]) + '\n')
outfile.close()

print("Complete!\n")
print(user_data)


