#!/usr/bin/env python

import glob

def run_stats(folder):
    print('\tin ' + str(folder))
    for filename in glob.glob(str(folder)+'/*.dat'):
        with open(filename, 'r') as f:
            rssi_sum = 0
            rssi_list = []
            rssi_count = 0
            time_start = 0
            time_end = 0
            for line in f:
                if line[0] == '#':
                    continue

                timestamp = line.split('\t')[0]
                if time_start == 0:
                    time_start = float(timestamp)
                time_end = float(timestamp)

                rssi = line.split('\t')[2].split('\n')[0]
                rssi_sum += float(rssi)
                rssi_list.append(float(rssi))
                rssi_count += 1

            duration = time_end-time_start
            rssi_avg = rssi_sum/float(rssi_count)
            rssi_med = 0
            if len(rssi_list)%2 == 0:
                rssi_med = ((sorted(rssi_list)[len(rssi_list)/2] + sorted(rssi_list)[len(rssi_list)/2+1]) / 2.0)
            else:
                rssi_med = sorted(rssi_list)[len(rssi_list)/2]

            print(str(filename) + ':\t' + str(duration) + '\t' + str(rssi_med))
            #print(str(filename) + ':\t' + str(duration) + '\t' + str(rssi_avg) + '\t\t' + str(rssi_med))

# print header
print('#filename\t\t\tduration\trssi_med#')

# all files in loc_close
run_stats('loc_close')

# all files in loc_far
run_stats('loc_far')

