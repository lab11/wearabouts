#!/usr/bin/env python

import sys
import time
import operator
import dataprint

infile = open('rssi_data_sorted.dat', 'r')

outfile = open('rssi_data_allRooms_count.dat', 'w')
out_data = []

in_header = True
line_num = 0

zero_time = 1429624973.000
curr_hour = 10
curr_min = 2
curr_sec = 53

start_time = 1429591142.59

rssi_timeout = 90
if len(sys.argv) >= 2:
    rssi_timeout = int(sys.argv[1])

rssi_threshold = -150
if len(sys.argv) >= 3:
    rssi_threshold = int(sys.argv[2])

# minimum number of samples
by_max_count = True
if len(sys.argv) >= 4:
    by_max_count = (sys.argv[3] == 'True')

min_sample_count = 28
if len(sys.argv) >= 5:
    min_sample_count = int(sys.argv[4])

scanner_mapping = {
        '1C:BA:8C:ED:ED:2A': ('University of Michigan|BBB|4908', '0'),
        '1C:BA:8C:9B:BC:57': ('University of Michigan|BBB|4901', '1'),
        'D0:39:72:4B:AD:14': ('University of Michigan|BBB|4670', '2'),
        '6C:EC:EB:A5:98:E2': ('University of Michigan|BBB|4916', '3'),
        '1C:BA:8C:ED:E0:B2': ('University of Michigan|BBB|4776', '4'),
        '6C:EC:EB:9F:70:53': ('USA|Michigan|Ann Arbor|1929 Plymouth', '5')
        }

people_mapping = {
        'ec:84:04:f4:4a:07': ('nealjack', 'Neal Jackson'),
        'e2:a7:7f:78:34:24': ('jhalderm', 'Alex Halderman'),
        'f9:97:1e:8b:e7:27': ('brghena', 'Branden Ghena'),
        'ee:b7:8c:0d:8d:4d': ('bradjc', 'Brad Campbell'),
        'e8:74:72:8f:e4:57': ('wwhuang', 'William Huang'),
        'ca:a3:bb:ea:94:5b': ('mclarkk', 'Meghan Clark'),
        'd1:c6:df:67:1c:60': ('rohitram', 'Rohit Ramesh'),
        'f0:76:0f:09:b8:63': ('nklugman', 'Noah Klugman'),
        'ec:6d:04:74:fa:69': ('yhguo', 'Yihua Guo'),
        'f4:bb:3c:af:99:6c': ('bpkempke', 'Ben Kempke'),
        'db:eb:52:c7:90:74': ('sdebruin', 'Sam DeBruin'),
        'f7:fd:9a:80:91:79': ('genevee', 'Genevieve Flaspohler'),
        'dc:fa:65:c7:cd:34': ('cfwelch', 'Charlie Welch'),
        'de:da:9c:f1:75:94': ('davadria', 'David Adrian'),
        'cd:49:fa:6a:98:b1': ('None', 'Spare Blue Force'),
        'ca:2d:39:50:f0:b1': ('ppannuto', 'Pat Pannuto'),
        'ee:47:fa:fe:ac:c2': ('evrobert', 'Eva Robert'),
        'c4:26:da:a4:72:c3': ('samkuo', 'Ye-Sheng Kuo'),
        'f1:7c:98:6e:b9:d1': ('jdejong', 'Jessica De Jong'),
        'e0:5e:5a:28:85:e3': ('tzachari', 'Thomas Zachariah'),
        'ca:28:2b:08:f3:f7': ('adkinsjd', 'Josh Adkins'),
        'fa:38:b5:a6:fe:6e': ('sarparis', 'Sarah Paris'),
        }

data_dict = {}

# only runs on a single person at a time
def locate(time, data, new_loc, selection_count):
    curr_loc = data['present_loc']

    # remove all data points that are no longer valid
    #   timeout is now signified by an empty list
    for loc in data:
        if loc == 'present_loc':
            continue

        while len(data[loc]['time']) > 0 and (time-data[loc]['time'][0]) > rssi_timeout:
            data[loc]['time'].pop(0)
            data[loc]['rssi'].pop(0)

    # find all possibly valid locations
    possible_locs = []
    for loc in data:
        if loc == 'present_loc':
            continue

        if len(data[loc]['time']) < min_sample_count:
            data[loc]['is_present'] = False
        else:
            data[loc]['is_present'] = True
            possible_locs.append(loc)

    if len(possible_locs) > 1:
        selection_count += 1

    # select between possibly valid locations
    highest_count = 0
    most_recent_time = 0
    best_loc = -1
    for loc in possible_locs:
        count = len(data[loc]['time'])
        if count > highest_count:
            highest_count = count
            most_recent_time = max(data[loc]['time'])
            best_loc = loc
        elif count == highest_count:
            if loc == curr_loc:
                # return current location if tied with best
                most_recent_time = max(data[loc]['time'])
                best_loc = loc
            elif best_loc != curr_loc:
                if max(data[loc]['time']) > most_recent_time:
                    # return best rssi with newest time
                    most_recent_time = data[loc]['time']
                    best_loc = loc
                elif max(data[loc]['time']) == most_recent_time and loc == new_loc:
                    # return best rssi with newest time and current incoming packet
                    best_loc = loc

    return (best_loc, selection_count)

selection_count = 0
for line in infile:
    line_num += 1

    # header or time notation data
    if line[0] == '#':
        # no data to record for this line
        continue

    data = line.split()
    timestamp = start_time + float(data[0])
    ble_addr = data[1]
    rssi = int(data[2])
    loc_id = int(data[3])
    uniqname = people_mapping[ble_addr][0]

    # only grab data from the appropriate time
    if timestamp < (zero_time - 1980) or timestamp > (zero_time + 43216):
        continue
    #if timestamp > (zero_time-1635):
    #    exit(1)
    #print("")
    #print("Data at: " + str(timestamp))

    # see if there were any timeouts since last timestamp
    for person in data_dict:
        # check if the present loc has timed out
        #   this needs to be a loop to handle cascading timeouts where the previous
        #   location is no longer valid, but a new one is
        change_time = 0
        if data_dict[person]['present_loc'] != -1:
            change_time = min(data_dict[person][data_dict[person]['present_loc']]['time'])
        while (data_dict[person]['present_loc'] != -1 and (timestamp-change_time) > rssi_timeout):

            # advance time to see if timeouts change location
            absent_time = change_time+rssi_timeout
            (new_loc, selection_count) = locate(absent_time+0.000001, data_dict[person], -1, selection_count)

            # check if something changed
            if new_loc != data_dict[person]['present_loc']:
                # change occurred. At point at old state
                timestr = time.strftime('%H:%M:%S', time.localtime(absent_time-0.000001))
                time_data = [timestr, (absent_time-zero_time-0.000001)]
                person_data = []
                for name in ['sarparis', 'samkuo', 'nealjack', 'adkinsjd', 'brghena', 'bpkempke']:
                    if name in data_dict:
                        person_data.append(data_dict[name]['present_loc'])
                    else:
                        person_data.append(-1)
                # record data
                out_data.append(time_data+person_data)

                # actually make the change
                absent_time += 0.000001
                data_dict[person]['present_loc'] = new_loc

                # add new data point
                timestr = time.strftime('%H:%M:%S', time.localtime(absent_time))
                time_data = [timestr, (absent_time-zero_time)]
                person_data = []
                for name in ['sarparis', 'samkuo', 'nealjack', 'adkinsjd', 'brghena', 'bpkempke']:
                    if name in data_dict:
                        person_data.append(data_dict[name]['present_loc'])
                    else:
                        person_data.append(-1)
                # record data
                out_data.append(time_data+person_data)

            # advance time step
            if new_loc != -1:
                change_time = min(data_dict[person][data_dict[person]['present_loc']]['time'])


    # valid data must be on campus
    #if loc_id not in [0]:
    if loc_id not in [0, 1, 2, 3, 4]:
        continue

    # data is valid, enter it
    if uniqname not in data_dict:
        data_dict[uniqname] = {'present_loc': -1}
    if loc_id not in data_dict[uniqname]:
        data_dict[uniqname][loc_id] = {'time': [0], 'rssi': [0]}
    data_dict[uniqname][loc_id]['time'].append(timestamp)
    data_dict[uniqname][loc_id]['rssi'].append(rssi)

    # see if things changed with new data point
    (new_loc, selection_count) = locate(timestamp, data_dict[uniqname], loc_id, selection_count)
    #print("New data: " + str(timestamp-zero_time) + ' ' + str(loc_id) + ' ' + str(rssi) + ' ' + str(new_loc))
    if new_loc != data_dict[uniqname]['present_loc']:
        # add a data point in the old state
        timestr = time.strftime('%H:%M:%S', time.localtime(timestamp-0.000001))
        time_data = [timestr, (timestamp-zero_time-0.000001)]
        person_data = []
        for person in ['sarparis', 'samkuo', 'nealjack', 'adkinsjd', 'brghena', 'bpkempke']:
            if person in data_dict:
                person_data.append(data_dict[person]['present_loc'])
            else:
                person_data.append(-1)
        # record data
        out_data.append(time_data+person_data)

        data_dict[uniqname]['present_loc'] = new_loc
        timestr = time.strftime('%H:%M:%S', time.localtime(timestamp))
        time_data = [timestr, (timestamp-zero_time)]
        person_data = []
        for person in ['sarparis', 'samkuo', 'nealjack', 'adkinsjd', 'brghena', 'bpkempke']:
            if person in data_dict:
                person_data.append(data_dict[person]['present_loc'])
            else:
                person_data.append(-1)
        # record data
        out_data.append(time_data+person_data)


# look for timeouts between end of data and end of time
timestamp = zero_time + 43216
for person in data_dict:
    # check if the present loc has timed out
    #   this needs to be a loop to handle cascading timeouts where the previous
    #   location is no longer valid, but a new one is
    change_time = 0
    if data_dict[person]['present_loc'] != -1:
        change_time = min(data_dict[person][data_dict[person]['present_loc']]['time'])
    while (data_dict[person]['present_loc'] != -1 and (timestamp-change_time) > rssi_timeout):

        # advance time to see if timeouts change location
        absent_time = change_time+rssi_timeout
        (new_loc, selection_count) = locate(absent_time+0.000001, data_dict[person], -1, selection_count)

        # check if something changed
        if new_loc != data_dict[person]['present_loc']:
            # change occurred. At point at old state
            timestr = time.strftime('%H:%M:%S', time.localtime(absent_time-0.000001))
            time_data = [timestr, (absent_time-zero_time-0.000001)]
            person_data = []
            for name in ['sarparis', 'samkuo', 'nealjack', 'adkinsjd', 'brghena', 'bpkempke']:
                if name in data_dict:
                    person_data.append(data_dict[name]['present_loc'])
                else:
                    person_data.append(-1)
            # record data
            out_data.append(time_data+person_data)

            # actually make the change
            absent_time += 0.000001
            data_dict[person]['present_loc'] = new_loc

            # add new data point
            timestr = time.strftime('%H:%M:%S', time.localtime(absent_time))
            time_data = [timestr, (absent_time-zero_time)]
            person_data = []
            for name in ['sarparis', 'samkuo', 'nealjack', 'adkinsjd', 'brghena', 'bpkempke']:
                if name in data_dict:
                    person_data.append(data_dict[name]['present_loc'])
                else:
                    person_data.append(-1)
            # record data
            out_data.append(time_data+person_data)

        # advance time step
        if new_loc != -1:
            change_time = min(data_dict[person][data_dict[person]['present_loc']]['time'])


# data has reached the end, place last point
timestr = time.strftime('%H:%M:%S', time.localtime(timestamp))
time_data = [timestr, (timestamp-zero_time)]
person_data = []
for name in ['sarparis', 'samkuo', 'nealjack', 'adkinsjd', 'brghena', 'bpkempke']:
    if name in data_dict:
        person_data.append(data_dict[name]['present_loc'])
    else:
        person_data.append(-1)
# record data
out_data.append(time_data+person_data)


# sort out_data by seconds column
out_data.sort(key=operator.itemgetter(1))
out_data.insert(0, ['#time', 'seconds', 'sarparis', 'samkuo', 'nealjack', 'adkinsjd', 'brghena', 'bpkempke'])

# print data to file
dataprint.to_file(outfile, out_data)

print("Complete")
print("Selection count: " + str(selection_count))
infile.close()
outfile.close()

