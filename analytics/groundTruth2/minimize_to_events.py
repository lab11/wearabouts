#!/usr/bin/env python

import dataprint

# updates files to add a new datapoint 0.000001 seconds before any transition
#   makes the data look like straight up/down transitions when plotted

data_files = [('camera/camera_parsed.dat', 'camera/camera_minimized.dat'),
        ('rfid/rfid_parsed.dat', 'rfid/rfid_minimized.dat'),
        ('wearabouts/wearabouts_parsed.dat', 'wearabouts/wearabouts_minimized.dat'),
        ('amalgamated_truth/first_amalgamated_dataset.dat', 'amalgamated_truth/amalgamated_plottable.dat'),
        ]

for filenames in data_files:
    infile = open(filenames[0], 'r')
    outfile = open(filenames[1], 'w')
    out_data = []

    first_line = True
    added_this_line = False
    truth_data = []

    for line in infile:
        added_this_line = False

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

        # other lines, skip if repetitive
        new_truth_data = line.split()[2:]
        if truth_data == new_truth_data:
            continue

        # print to file if new event
        out_data.append(line.split())
        added_this_line = True

        # update truth data
        truth_data = new_truth_data

    # append the last line of the file
    if not added_this_line:
        out_data.append(line.split())

    dataprint.to_file(outfile, out_data)
    infile.close()
    outfile.close()

