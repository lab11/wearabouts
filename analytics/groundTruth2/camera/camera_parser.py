#!/usr/bin/env python

import dataprint

infile = open('camera_raw.dat', 'r')
outfile = open('camera_parsed.dat', 'w')

out_data = []
#out_data.append(['#time', 'seconds', 'samkuo', 'brghena', 'azhen', 'bradjc', 'wwhuang', 'ppannuto', 'sdebruin', 'bpkempke', 'mclarkk', 'rohitram'])
out_data.append(['#time', 'seconds', 'samkuo', 'brghena', 'azhen', 'bradjc', 'wwhuang', 'ppannuto', 'sdebruin', 'bpkempke', 'mclarkk', 'rohitram', 'tzachari', 'nklugman', 'sairohit'])

total_people = 13
start_hour = 18
start_min = 27
start_sec = 43

line_num = 0
error = False
prev_diff_seconds = -1
curr_day = 0
curr_hour = start_hour
curr_min = start_min
curr_sec = start_sec
truth_data = []

# parse data from file
# goal is to take the raw file and turn it into a data point at each minute, with data for each name
# also check file for errors while you're parsing it
for line in infile:
    line_num += 1

    # header, comment, or time notation data
    if line[0] == '#':
        if line[1] == '#':
            # stop parsing. Useful for debugging
            if line == '## STOP\n':
                print("File parsing STOPPED")
                break
            # it is a header or comment, ignore
            continue
        else:
            print("Time annotation, Line: " + str(line_num))
            # new time notation
            time_data = line.split(' ')[1].split(':')
            new_hour = int(time_data[0])
            new_min  = int(time_data[1])
            new_sec  = int(time_data[2])

            # check for errors. A bit data-specific
            if ((new_hour < curr_hour and curr_hour != 23) or
                    (new_min < curr_min and new_hour == curr_hour) or
                    (new_sec < curr_sec and new_hour == curr_hour and new_min == curr_min)):
                # check if everything is okay and this was one of the time resets
                if new_sec < curr_sec and line[-6:-1] != ' Leap':
                    print("Error at line: " + str(line_num))
                    break
            if (new_sec != curr_sec and line[-6:-1] != ' Leap'):
                print("Mistaken leap second? " + str(line_num))
                break
            print("Old time= " + str(curr_hour) + ':' + str(curr_min) + ':' + str(curr_sec) + "\tNew time= " + str(new_hour) + ':' + str(new_min) + ':' + str(new_sec))

            # seems valid. Replicate previous data until the minute before now
            while (curr_hour < new_hour or curr_min < new_min or (curr_hour == 23 and curr_hour > new_hour)):
                # generate time data for this line
                curr_time = (('0' if curr_hour < 10 else '' ) + str(curr_hour) + ':' +
                        ('0' if curr_min < 10 else '') + str(curr_min) + ':' +
                        ('0' if curr_sec < 10 else '') + str(curr_sec))
                diff_seconds = (curr_day)*24*3600 + (curr_hour-start_hour)*3600 + (curr_min-start_min)*60 + (curr_sec-start_sec)
                time_data = [curr_time, diff_seconds]
                # error check
                if diff_seconds <= prev_diff_seconds and curr_hour != 23:
                    print("Error, backwards time in annotation: " + str(line_num))
                    error = True
                    break
                prev_diff_seconds = diff_seconds

                # record data
                out_data.append(time_data+truth_data)

                # increment time
                curr_min += 1
                if curr_min == 60:
                    curr_min = 0
                    curr_hour += 1
                    if curr_hour == 24:
                        curr_hour = 0
                        curr_day += 1

            if error:
                # error already printed
                break

            # update time
            curr_hour = new_hour
            curr_min = new_min
            curr_sec = new_sec

            # done with annotation
            continue

    print("Normal data, Line: " + str(line_num))
    # normal data, list of people and presence
    truth_data = line.split(' ')
    while len(truth_data) != total_people:
        truth_data.append(0)
    # convert to room id: -1 for unknown, 0 for 4908
    truth_data = [int(item)-1 for item in truth_data]

    # generate time data for this line
    curr_time = (('0' if curr_hour < 10 else '') + str(curr_hour) + ':' +
            ('0' if curr_min < 10 else '') + str(curr_min) + ':' +
            ('0' if curr_sec < 10 else '') + str(curr_sec))
    diff_seconds = (curr_day)*24*3600 + (curr_hour-start_hour)*3600 + (curr_min-start_min)*60 + (curr_sec-start_sec)
    time_data = [curr_time, diff_seconds]
    # error check
    if diff_seconds <= prev_diff_seconds and curr_hour != 23:
        print("Error, backwards time in normal: " + str(line_num))
        break
    prev_diff_seconds = diff_seconds

    # record data
    out_data.append(time_data+truth_data)

    # increment time
    curr_min += 1
    if curr_min == 60:
        curr_min = 0
        curr_hour += 1
        if curr_hour == 24:
            curr_hour = 0
            curr_day += 1
else:
    print("Complete!")


# print data to file
dataprint.to_file(outfile, out_data)

infile.close()
outfile.close()

