#!/usr/bin/env python

# Records presence as if only 4908 has a scanner
#   with present meaning any packet seen in the last minute
#   with absent meaning no packet seen in the last minute

import sys
import time
import operator
import dataprint

infile = open('rssi_data.dat', 'r')

outfile = open('rssi_data_4908only_seen.dat', 'w')
out_data = []

in_header = True
line_num = 0

zero_time = 1429624973.000
curr_hour = 10
curr_min = 2
curr_sec = 53

start_time = 1429591142.59

rssi_timeout = 60
if len(sys.argv) == 2:
    rssi_timeout = int(sys.argv[1])

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

    # update presences based on the current time
    for person in data_dict:
        if data_dict[person]['present_loc'] != -1:
            still_present = False
            absent_time = 0
            for loc in data_dict[person]:
                if loc == 'present_loc':
                    continue

                if (timestamp-data_dict[person][loc]['time']) < rssi_timeout:
                    still_present = True
                else:
                    data_dict[person][loc]['is_present'] = False
                    if absent_time < (data_dict[person][loc]['time']+rssi_timeout):
                        absent_time = data_dict[person][loc]['time']+rssi_timeout

            if not still_present:
                # add a data point when the user was still present
                timestr = time.strftime('%H:%M:%S', time.localtime(absent_time-1))
                time_data = [timestr, (absent_time-zero_time-1)]
                person_data = []
                for name in ['sarparis', 'samkuo', 'nealjack', 'adkinsjd', 'brghena', 'bpkempke']:
                    if name in data_dict:
                        person_data.append(data_dict[name]['present_loc'])
                    else:
                        person_data.append(-1)
                # record data
                out_data.append(time_data+person_data)

                # add a new data point for user absent
                data_dict[person]['present_loc'] = -1
                timestr = time.strftime('%H:%M:%S', time.localtime(absent_time))
                time_data = [timestr, (absent_time-zero_time)]
                person_data = []
                for name in ['sarparis', 'samkuo', 'nealjack', 'adkinsjd', 'brghena', 'bpkempke']:
                    if name in data_dict:
                        person_data.append(data_dict[name]['present_loc'])
                    else:
                        person_data.append(-1)
                # record data
                # Note: this has the possibility of appending data that is out
                #   of order in time. out_data will be sorted later to deal
                #   with this
                out_data.append(time_data+person_data)


    # only grab data for 4908
    if loc_id != 0:
        continue

    # data is valid, enter it
    if uniqname not in data_dict:
        data_dict[uniqname] = {'present_loc': -1}
    if loc_id not in data_dict[uniqname]:
        data_dict[uniqname][loc_id] = {'time': 0, 'rssi': [0]}
    data_dict[uniqname][loc_id]['time'] = timestamp
    data_dict[uniqname][loc_id]['rssi'] = rssi
    data_dict[uniqname][loc_id]['is_present'] = True

    # add to output if the state has changed
    if data_dict[uniqname]['present_loc'] == -1:
        # record data for the user absent
        timestr = time.strftime('%H:%M:%S', time.localtime(timestamp-1))
        time_data = [timestr, (timestamp-zero_time-1)]
        person_data = []
        for person in ['sarparis', 'samkuo', 'nealjack', 'adkinsjd', 'brghena', 'bpkempke']:
            if person in data_dict:
                person_data.append(data_dict[person]['present_loc'])
            else:
                person_data.append(-1)
        # record data
        out_data.append(time_data+person_data)

        data_dict[uniqname]['present_loc'] = loc_id
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

# add final line to file
timestamp = zero_time + 43216
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

# sort out_data by seconds column
out_data.sort(key=operator.itemgetter(1))
out_data.insert(0, ['#time', 'seconds', 'sarparis', 'samkuo', 'nealjack', 'adkinsjd', 'brghena', 'bpkempke'])

# print data to file
dataprint.to_file(outfile, out_data)

print("Complete")
infile.close()
outfile.close()

