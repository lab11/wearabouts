#!/usr/bin/env python

import dataprint
import ast
import json
import time

scanner_mapping = {
            '1C:BA:8C:ED:ED:2A': ('University of Michigan|BBB|4908', '0'),
            '1C:BA:8C:9B:BC:57': ('University of Michigan|BBB|4901', '1'),
            'D0:5F:B8:FE:47:BB': ('University of Michigan|BBB|4670', '2'),
            'D0:39:72:30:71:3E': ('University of Michigan|BBB|4916', '3'),
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
        #'ca:28:2b:08:f3:f7': ('adkinsjd', 'Josh Adkins'),
        'ca:28:2b:08:f3:f7': ('sairohit', 'Sai Gouravajhala'),
        'fa:38:b5:a6:fe:6e': ('sarparis', 'Sarah Paris'),
        'c8:ee:59:3a:a0:16': ('azhen', 'Alan Zhen'),
        'dd:b3:e2:6d:92:2b': ('ppannuto_hr', 'Pat Pannuto HR'),
        }

infile = open('gatd_extract.dat', 'r')

out_datas = {}
people_list = ['samkuo', 'brghena', 'azhen', 'bradjc', 'sdebruin', 'sairohit']
out_datas = dict((person, [['#timestamp', 'location ID', 'uniqname', 'rssi']]) for person in people_list)
packet_num = 0

for line in infile:
    # read in as dict
    data = ast.literal_eval(line.replace('ObjectId', ''))
    if data['ble_addr'] in people_mapping:
        data['uniqname'] = people_mapping[data['ble_addr']][0]
    else:
        continue
    data['location_id'] = scanner_mapping[data['scanner_macAddr']][1]

    # print intermittent status updates
    packet_num += 1
    if (packet_num % 1000) == 0:
        print("Status: " + time.strftime("%m/%d %H:%M:%S", time.localtime(data['time']/1000)))

    if data['uniqname'] in people_list:
        out_datas[data['uniqname']].append([data['time'], data['location_id'], data['uniqname'], data['rssi']])


print("Data collection complete, printing to files...")
for person in people_list:
    outfile = open(str(person) + '_ble.dat', 'w')
    dataprint.to_file(outfile, out_datas[person])
    outfile.close()

