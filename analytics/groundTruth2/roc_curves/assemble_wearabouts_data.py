#!/usr/bin/env python

# steps:
#X  run wearabouts on each person with given BLE_DURATION and BLE_MINIMUM_COUNT
#X  combine files from individuals into a single file equivalent to real wearabouts files
#       (compare against real file to ensure this is working...)
#O  run accuracy comparison on wearabouts results vs amalgamated data

import sys
import dataprint
import time
import glob
import copy

# 72 hours total
start_time = 1937 # Day 1, 19:00
end_time = 261137 # Day 4, 19:00
start_timestamp = 1441060063

people_list = ['samkuo', 'brghena', 'azhen', 'bradjc', 'wwhuang', 'ppannuto', 'sdebruin', 'bpkempke', 'mclarkk', 'rohitram', 'tzachari', 'nklugman', 'sairohit']
users = {'samkuo': 2, 'brghena': 3, 'azhen': 4, 'bradjc': 5, 'sdebruin': 8, 'sairohit': 14}

input_files = sorted(glob.glob('results/*_wearabouts.dat'))

# assemble a dataset of all the wearabouts data, sorted by time
input_data = []
for input_file in input_files:
    infile = open(input_file, 'r')
    user_data = [line.split() + [input_file.split('_')[0].split('/')[1]] for line in infile.readlines()[1:]]
    user_data = [[str(a), float(b), int(c), str(d)] for (a,b,c,d) in user_data]
    input_data += user_data
    infile.close()
input_data.sort(key=lambda arr: arr[1])
print("Dataset assembled")

outfile = open('results/assembled_dataset.dat', 'w')
out_data = []
out_data.append(['#time', 'seconds', 'samkuo', 'brghena', 'azhen', 'bradjc', 'wwhuang', 'ppannuto', 'sdebruin', 'bpkempke', 'mclarkk', 'rohitram', 'tzachari', 'nklugman', 'sairohit'])

prev_line = ['00:00:00', 0.0] + [-1]*len(people_list)
for line in input_data:
    # check dataset for duplicates
    if prev_line[1] == line[1]:
        print("Duplicates found!\n\t" + str(prev_line) + '\n\t' + str(line))
        exit()

    # modify line with new data
    data_index = users[line[-1]]
    new_line = copy.copy(prev_line)
    new_line[0] = line[0]
    new_line[1] = line[1]
    new_line[data_index] = line[2]
    prev_line = new_line

    # write line to output
    out_data.append(new_line)
dataprint.to_file(outfile, out_data)
outfile.close()
print("Written to file!")

