#!/usr/bin/env python

import ast

infile = open('gatd_data.packets', 'r')
outfile = open('apartment.dat', 'w')

lines_in_file = 235238
earliest_data = 1428948000000
target_ble_addr = 'f9:97:1e:8b:e7:27'

first = True
start_time = 1428948000000
line_num = 0.0

for line in infile:
    # convert line into a dict
    # Note: the line has an object reference that is broken and must be removed
    pkt = ast.literal_eval(line.replace('ObjectId', ''))
    line_num += 1

    # print progress to user
    if line_num%1000 == 0:
        print("Progress: " + str(round(line_num/lines_in_file*100)) + '%')
    
    # skip data until we get to April 13th
    #   also skip packets that aren't the correct device
    if ('time' not in pkt or pkt['time'] < earliest_data or
            'ble_addr' not in pkt or pkt['ble_addr'] != target_ble_addr):
        continue

    # write header to outfile
    if first:
        first = False
        #start_time = float(pkt['time'])
        outfile.write("# 1929 Plymouth Road, device: '" + str(target_ble_addr) + "' time starts at: " + str(start_time) + '\n')
        outfile.write("# time\trssi\n")
        print("Data start found!")

    # write data to file
    outfile.write(str(float(pkt['time'])-start_time) + '\t' + str(pkt['rssi']) + '\n')

infile.close()
outfile.close()

