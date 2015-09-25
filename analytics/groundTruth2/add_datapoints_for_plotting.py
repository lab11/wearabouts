#!/usr/bin/env python

import dataprint

# updates files to add a new datapoint 0.000001 seconds before any transition
#   makes the data look like straight up/down transitions when plotted

data_files = [('camera/camera_parsed.dat', 'camera/camera_plottable.dat'),
        ('rfid/rfid_parsed.dat', 'rfid/rfid_plottable.dat'),
        ('wearabouts/wearabouts_parsed.dat', 'wearabouts/wearabouts_plottable.dat')]

time_quanta = 0.000001

for filenames in data_files:
    infile = open(filenames[0], 'r')
    outfile = open(filenames[1], 'w')
    out_data = []

    first_line = True
    truth_data = []

    for line in infile:
        # comment, copy straight
        if line[0] == '#':
            out_data.append(line.split())
            continue

        # first line, no changes needed, save state
        if first_line:
            first_line = False
            out_data.append(line.split())
            truth_data = line.split()[2:]
            continue

        # other lines, skip if repetitive, add point if new
        new_truth_data = line.split()[2:]
        if truth_data == new_truth_data:
            continue
        time_data = line.split()[0:2]
        time_data[1] = str(float(time_data[1]) - time_quanta)

        # print to file
        out_data.append(time_data+truth_data)
        out_data.append(line.split())

        # update truth data
        truth_data = new_truth_data

    # append the last line of the file
    out_data.append(line.split())

    dataprint.to_file(outfile, out_data)
    infile.close()
    outfile.close()

