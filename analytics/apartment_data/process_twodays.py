#!/usr/bin/env python

import ast

infile = open('twodays_raw.dat', 'r')
outfile = open('twodays.dat', 'w')

target_ble_addr = 'f9:97:1e:8b:e7:27'
start_time = 1428948000000

lines_in_file = 27954

first = True
line_num = 0.0
prev_time = 0

rssi_window_len = 50
rssi_window = [-200]*rssi_window_len
rssi_window_index = 0

time_window_len = 50
time_window = [0]*time_window_len
time_window_index = 0

for line in infile:
    # skip header
    if line[0] == '#':
        continue

    # convert line into array
    time_diff = float(line.split('\t')[0])
    rssi = int(line.split('\t')[1])

    # print progress to user
    line_num += 1
    if line_num%1000 == 0:
        print("Progress: " + str(round(line_num/lines_in_file*100)) + '%')
    
    # write header to outfile
    if first:
        first = False
        prev_time = time_diff
        outfile.write("# 1929 Plymouth Road, device: '" + str(target_ble_addr) + "' time starts at: " + str(start_time) + '\n')
        outfile.write("# time\trssi\ttime_diff\n")

    # create data
    time_window[time_window_index] = ((time_diff-prev_time)/1000)
    time_window_index = (time_window_index+1)%len(time_window)
    avg_time_diff = sum(time_window)/len(time_window)
    rssi_window[rssi_window_index] = rssi
    rssi_window_index = (rssi_window_index+1)%len(rssi_window)
    avg_rssi = sum(rssi_window)/len(rssi_window)

    # write data to file
    outfile.write(str(time_diff) + '\t' + str(rssi) + '\t' + str((time_diff-prev_time)/1000) + '\t' + 
            str(avg_time_diff) + '\t' + str(avg_rssi) + '\n')
    prev_time = time_diff

infile.close()
outfile.close()

