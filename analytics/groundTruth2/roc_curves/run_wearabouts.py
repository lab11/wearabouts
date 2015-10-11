#!/usr/bin/env python

# steps:
#X  run wearabouts on each person with given BLE_DURATION and BLE_MINIMUM_COUNT
#O  combine files from individuals into a single file equivalent to real wearabouts files
#       (compare against real file to ensure this is working...)
#O  run accuracy comparison on wearabouts results vs amalgamated data

import sys
import dataprint
import time
import glob

#TODO: set these from argv
BLE_DURATION = 75
BLE_MINIMUM_COUNT = 12
DEBUG = False

if len(sys.argv) == 3:
    BLE_DURATION = int(sys.argv[1])
    BLE_MINIMUM_COUNT = int(sys.argv[2])

# 72 hours total
start_time = 1937 # Day 1, 19:00
end_time = 261137 # Day 4, 19:00
start_timestamp = 1441060063

users = {'samkuo': 2, 'brghena': 3, 'azhen': 4, 'bradjc': 5, 'sdebruin': 8, 'sairohit': 14}

input_files = sorted(glob.glob('*_ble.dat'))
#input_files = ['brghena_ble.dat']

for filename in input_files:
    print("In file: " + str(filename))
    infile = open(filename, 'r')
    out_data = []
    out_data.append(['#time', 'seconds', filename.split('_')[0]])
    outfile = open('results/' + filename.split('_')[0]+'_wearabouts.dat', 'w')

    # for each data element that comes in
    #   remove all data that expired before this new timestamp
    #   apply new data
    #   determine if location changed
    #       if so, record a timestamp, location_id point

    curr_time = 0
    presences = {}
    curr_loc = -1
    line_num = 0
    for line in infile:
        line_num += 1
        if line[0] == '#':
            continue

        # import data from file
        data = line.split()
        diff_time = float(data[0])/1000 - start_timestamp
        location_id = int(data[1])
        uniqname = data[2]
        rssi = int(data[3])

        DEBUG = False
        if False and 235600 < diff_time < 235830:
            DEBUG = True
            print('--packet--')

        # status update
        if (line_num%1000) == 0 and DEBUG:
            print("\tStatus: " + time.strftime('%m/%d/%Y %H:%M:%S', time.localtime(diff_time+start_timestamp)))

        # handle timeouts
        while True:
            # find packet that should decay
            min_time = (diff_time-BLE_DURATION)
            min_loc = -1
            for loc in presences:
                if len(presences[loc]['times']) > 0 and presences[loc]['times'][0] < min_time:
                    min_time = presences[loc]['times'][0]
                    min_loc = loc
            if min_loc == -1:
                break
            else:
                # there is a packet that should decay
                curr_time = min_time+BLE_DURATION+0.000001 # the time at which it actually decays
                presences[min_loc]['times'].pop(0)
                presences[min_loc]['rssis'].pop(0)

                if DEBUG:
                    print('\t-' + str(len(presences[0]['times'])) + ' ' + str(presences[0]['times']))

                # recalculate average rssi values
                for loc in sorted(presences.keys()):
                    if len(presences[loc]['times']) > BLE_MINIMUM_COUNT:
                        presences[loc]['avg_rssi'] = sum(presences[loc]['rssis'])/len(presences[loc]['rssis'])
                    else:
                        presences[loc]['avg_rssi'] = -200

                # debug, more data
                if DEBUG:
                    out_str = time.strftime('-%m/%d/%Y %H:%M:%S', time.localtime(curr_time+start_timestamp)) + '  '
                    for loc in sorted(presences.keys()):
                        out_str += str(presences[loc]['avg_rssi']) + '\t'
                    print(out_str)

                # redetermine state
                best_locs = []
                best_rssi = -199
                for loc in presences:
                    if presences[loc]['avg_rssi'] > best_rssi:
                        best_rssi = presences[loc]['avg_rssi']
                for loc in sorted(presences.keys()):
                    if presences[loc]['avg_rssi'] == best_rssi:
                        best_locs.append(loc)
                # select from possible bests
                new_loc = -1
                if len(best_locs) == 0:
                    new_loc = -1
                #elif len(best_locs) == 1:
                #    new_loc = best_locs[0]
                elif curr_loc in best_locs:
                    #print("Note: Persisted in current location")
                    new_loc = curr_loc
                else:
                    # select based on most recently received packet
                    if len(best_locs) != 1:
                        print("Note: Choosing by most recent packet")
                    most_recent_time = 0
                    most_recent_loc = -1
                    for loc in best_locs:
                        if max(presences[loc]['times']) == most_recent_time:
                            print("Note: Choosing by room ordering")
                        if max(presences[loc]['times']) > most_recent_time:
                            most_recent_time = max(presences[loc]['times'])
                            most_recent_loc = loc
                    new_loc = most_recent_loc

                # record data if it has changed
                if new_loc != curr_loc:
                    if DEBUG:
                        print("Moved to location: " + str(new_loc) + '\n')
                    curr_loc = new_loc
                    out_data.append([time.strftime('%H:%M:%S', time.localtime(curr_time+start_timestamp)),
                            curr_time, curr_loc])

        # timeouts complete, handle the packet
        if location_id not in presences:
            presences[location_id] = {
                    'times': [],
                    'rssis': [],
                    'avg_rssi': -200,
                    }
        #presences[location_id]['times'].append(int(round(diff_time)))
        presences[location_id]['times'].append(diff_time)
        presences[location_id]['rssis'].append(rssi)
        curr_time = diff_time

        if DEBUG:
            print('\t' + str(len(presences[0]['times'])) + ' ' + str(presences[0]['times']))

        # recalculate average rssi values
        for loc in sorted(presences.keys()):
            if len(presences[loc]['times']) > BLE_MINIMUM_COUNT:
                presences[loc]['avg_rssi'] = sum(presences[loc]['rssis'])/len(presences[loc]['rssis'])
            else:
                presences[loc]['avg_rssi'] = -200

        # debug, more data
        if DEBUG:
            out_str = time.strftime('%m/%d/%Y %H:%M:%S', time.localtime(curr_time+start_timestamp)) + '  '
            for loc in sorted(presences.keys()):
                out_str += str(presences[loc]['avg_rssi']) + '\t'
            print(out_str)

        # redetermine state
        best_locs = []
        best_rssi = -199
        for loc in presences:
            if presences[loc]['avg_rssi'] > best_rssi:
                best_rssi = presences[loc]['avg_rssi']
        for loc in sorted(presences.keys()):
            if presences[loc]['avg_rssi'] == best_rssi:
                best_locs.append(loc)
        # select from possible bests
        new_loc = -1
        if len(best_locs) == 0:
            new_loc = -1
        #elif len(best_locs) == 1:
        #    new_loc = best_locs[0]
        elif curr_loc in best_locs:
            #print("Note: Persisted in current location")
            new_loc = curr_loc
        else:
            # select based on most recently received packet
            if len(best_locs) != 1:
                print("Note: Choosing by most recent packet")
            most_recent_time = 0
            most_recent_loc = -1
            for loc in best_locs:
                if max(presences[loc]['times']) == most_recent_time:
                    print("Note: Choosing by room ordering")
                if max(presences[loc]['times']) > most_recent_time:
                    most_recent_time = max(presences[loc]['times'])
                    most_recent_loc = loc
            new_loc = most_recent_loc

        # record data if it has changed
        if new_loc != curr_loc:
            if DEBUG:
                print("Moved to location: " + str(new_loc) + '\n')
            curr_loc = new_loc
            out_data.append([time.strftime('%H:%M:%S', time.localtime(curr_time+start_timestamp)),
                    curr_time, curr_loc])

    # handle remaining timeouts, anything that happened before the end time
    # picked a time where everyone should have timed out before this, except
    #   people who still get packets after it
    diff_time = 265000
    while True:
        # find packet that should decay
        min_time = (diff_time-BLE_DURATION)
        min_loc = -1
        for loc in presences:
            if len(presences[loc]['times']) > 0 and presences[loc]['times'][0] < min_time:
                min_time = presences[loc]['times'][0]
                min_loc = loc
        if min_loc == -1:
            break
        else:
            # there is a packet that should decay
            curr_time = min_time+BLE_DURATION+0.000001 # the time at which it actually decays
            presences[min_loc]['times'].pop(0)
            presences[min_loc]['rssis'].pop(0)

            if DEBUG:
                print('\t-' + str(len(presences[0]['times'])) + ' ' + str(presences[0]['times']))

            # recalculate average rssi values
            for loc in sorted(presences.keys()):
                if len(presences[loc]['times']) > BLE_MINIMUM_COUNT:
                    presences[loc]['avg_rssi'] = sum(presences[loc]['rssis'])/len(presences[loc]['rssis'])
                else:
                    presences[loc]['avg_rssi'] = -200

            # debug, more data
            if DEBUG:
                out_str = time.strftime('-%m/%d/%Y %H:%M:%S', time.localtime(curr_time+start_timestamp)) + '  '
                for loc in sorted(presences.keys()):
                    out_str += str(presences[loc]['avg_rssi']) + '\t'
                print(out_str)

            # redetermine state
            best_locs = []
            best_rssi = -199
            for loc in presences:
                if presences[loc]['avg_rssi'] > best_rssi:
                    best_rssi = presences[loc]['avg_rssi']
            for loc in sorted(presences.keys()):
                if presences[loc]['avg_rssi'] == best_rssi:
                    best_locs.append(loc)
            # select from possible bests
            new_loc = -1
            if len(best_locs) == 0:
                new_loc = -1
            #elif len(best_locs) == 1:
            #    new_loc = best_locs[0]
            elif curr_loc in best_locs:
                #print("Note: Persisted in current location")
                new_loc = curr_loc
            else:
                # select based on most recently received packet
                if len(best_locs) != 1:
                    print("Note: Choosing by most recent packet")
                most_recent_time = 0
                most_recent_loc = -1
                for loc in best_locs:
                    if max(presences[loc]['times']) == most_recent_time:
                        print("Note: Choosing by room ordering")
                    if max(presences[loc]['times']) > most_recent_time:
                        most_recent_time = max(presences[loc]['times'])
                        most_recent_loc = loc
                new_loc = most_recent_loc

            # record data if it has changed
            if new_loc != curr_loc:
                if DEBUG:
                    print("Moved to location: " + str(new_loc) + '\n')
                curr_loc = new_loc
                out_data.append([time.strftime('%H:%M:%S', time.localtime(curr_time+start_timestamp)),
                        curr_time, curr_loc])

    dataprint.to_file(outfile, out_data)
    infile.close()
    outfile.close()
    #DEBUG
    if DEBUG:
        exit()

