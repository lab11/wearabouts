#!/usr/bin/env python

import dataprint

infile = open('ground_truth_raw.dat', 'r')
outfile = open('ground_truth_parsed.dat', 'w')

out_data = []
out_data.append(['#time', 'seconds', 'sarparis', 'samkuo', 'nealjack', 'adkinsjd', 'brghena', 'bpkempke'])

in_header = True
line_num = 0
curr_hour = 9
curr_min = 30
curr_sec = 53

# add data from before parsing starts
while curr_min != 2:
    curr_time = str(curr_hour) + ':' + str(curr_min) + ':' + str(curr_sec)
    diff_seconds = (curr_hour-10)*3600 + (curr_min-2)*60 + (curr_sec-53)
    time_data = [curr_time, diff_seconds]

    # update time
    curr_min += 1
    if curr_min == 60:
        curr_min = 0
        curr_hour += 1

    # record data
    out_data.append(time_data+[-1]*6)

if curr_hour != 10 or curr_min != 2 or curr_sec != 53:
    print("ERROR!!!")
    exit(1)

# parse data from file
for line in infile:
    line_num += 1

    # header or time notation data
    if line[0] == '#':
        if in_header:
            # look for end of header
            if line == '#\n':
                in_header = False
        else:
            # update current second. Handle minute overflow
            time_data = line.split(' ')[1].split(':')
            if curr_sec == 59 and int(time_data[2]) == 0:
                curr_min += 1
            curr_sec = int(time_data[2])

            # update timestamp
            if curr_hour != int(time_data[0]) or curr_min != int(time_data[1]):
                print("Error at line: " + str(line_num) +
                        "\nTime expected " + str(curr_hour) + ':' + str(curr_min) + ':' + str(curr_sec) +
                        "\nTime found    " + str(time_data[0]) + ':' + str(time_data[1]) + ':' + str(time_data[2]))
                break

        # no data to record for this line
        continue

    # ground truth data
    truth_data = line.split(' ')
    while len(truth_data) != 6:
        truth_data.append(0)
    truth_data = [int(item)-1 for item in truth_data]

    # time data
    curr_time = str(curr_hour) + ':' + str(curr_min) + ':' + str(curr_sec)
    diff_seconds = (curr_hour - 10)*3600 + (curr_min - 2)*60 + (curr_sec - 53)
    time_data = [curr_time, diff_seconds]

    # update time
    curr_min += 1
    if curr_min == 60:
        curr_min = 0
        curr_hour += 1

    # record data
    out_data.append(time_data+truth_data)
else:
    print("Complete!")


# print data to file
dataprint.to_file(outfile, out_data)

infile.close()
outfile.close()

