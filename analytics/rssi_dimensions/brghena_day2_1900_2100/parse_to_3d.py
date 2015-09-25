#!/usr/bin/env python

import dataprint

infile = open('rssi_view.dat', 'r')
outfile = open('rssi_3d.dat', 'w')

out_dicts = [{}*5]
out_data = []

out_data.append([
        '#4908 rssi', '#4901 rssi', 'count',
        '#4908 rssi', '#4901 rssi', 'count',
        '#4908 rssi', '#4670 rssi', 'count',
        '#4908 rssi', '#4916 rssi', 'count',
        '#4908 rssi', '#4776 rssi', 'count',
    ])
x_data = 1 # 4908

line_num = 0
for line in infile:
    line_num += 1

    if line[0] == '#':
        print("skipping comment " + str(line_num))
        continue

    data = [int(item) for item in line.split()]
    xdat = data[x_data]
    index = 0
    for index in range(5):
        out_dict = out_dicts[index]
        ydats = data[2+index:2+index+1]
        #ydats = data[2:] # all rooms
        #ydats = data[3:4] # room 4670

        if xdat == -200:
            print("skipping line " + str(line_num))
            continue

        for ydat in ydats:
            if ydat == -200:
                continue

            if xdat not in out_dict:
                out_dict[xdat] = {}
            if ydat not in out_dict[xdat]:
                out_dict[xdat][ydat] = 0
            out_dict[xdat][ydat] += 1


#XXX: need to figure out how to make all 5 datas go into single file
for out_dict in out_dicts:
for xdat in sorted(out_dict.keys()):
    for ydat in sorted(out_dict[xdat].keys()):
        out_data.append([xdat, ydat, out_dict[xdat][ydat]])

print("Complete")
dataprint.to_file(outfile, out_data)
infile.close()
outfile.close()

