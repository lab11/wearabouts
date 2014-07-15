#!/usr/bin/env python2

import csv
import matplotlib.pyplot as plt

labmembers = ['bradjc', 'brghena', 'samkuo', 'tzachari', 'wwhuang']

# read in both csv files
groundtruth_dict = {}
whereabouts_dict = {}
with open('ground_truth.data') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
        if row[0][0] == '#':
            continue
        else:
            groundtruth_dict[int(row[0])] = row[1:]

with open('whereabouts.data') as csvfile:
    reader = csv.reader(csvfile, delimiter=',')
    for row in reader:
        if row[0][0] == '#':
            continue
        else:
            whereabouts_dict[int(row[0])] = row[1:]

total_timestamps = len(groundtruth_dict.keys())
accuracy_dict = {'bradjc': 0, 'brghena': 0, 'samkuo': 0, 'tzachari': 0, 'wwhuang': 0}
strict_total = {'bradjc': 0, 'brghena': 0, 'samkuo': 0, 'tzachari': 0, 'wwhuang': 0}
strict_dict = {'bradjc': 0, 'brghena': 0, 'samkuo': 0, 'tzachari': 0, 'wwhuang': 0}
for timestamp in sorted(groundtruth_dict.keys()):
    if timestamp not in whereabouts_dict:
        print("Bad timestamp")
        exit()

    for index in range(len(labmembers)):
        if groundtruth_dict[timestamp][index] == '1' or whereabouts_dict[timestamp][index] == '1':
            strict_total[labmembers[index]] += 1

        if groundtruth_dict[timestamp][index] == whereabouts_dict[timestamp][index]:
            accuracy_dict[labmembers[index]] += 1

            if groundtruth_dict[timestamp][index] == '1' or whereabouts_dict[timestamp][index] == '1':
                strict_dict[labmembers[index]] += 1

for person in labmembers:
    print(person + ': ' + str(accuracy_dict[person]) + " correct out of " +
            str(total_timestamps) + "  [" + str(accuracy_dict[person]/float(total_timestamps)) +
            "%]\t" + str(strict_dict[person]) + '/' + str(strict_total[person]) + "  [" +
            str(strict_dict[person]/float(strict_total[person])) + "%] strict")


# process and plot data
if True:
    f, axarr = plt.subplots(len(labmembers), sharex=True)
    axarr[0].set_title('Whereabouts Accuracy - 4908 BBB - 7/8/2014 9:35 to 21:35')

    #axarr[-1].set_ylabel('Presence')
    axarr[-1].set_xlabel('Time (hour of day)')

    plot_xdata = []
    plot_groundtruth_ydata = [[] for _ in range(len(labmembers))]
    plot_whereabouts_ydata = [[] for _ in range(len(labmembers))]
    for timestamp in sorted(groundtruth_dict.keys()):
        plot_xdata.append(timestamp)

        for index in range(len(labmembers)):
            plot_groundtruth_ydata[index].append(int(groundtruth_dict[timestamp][index]))

    for timestamp in sorted(whereabouts_dict.keys()):
        if timestamp not in plot_xdata:
            print("Timestamp mismatch!")
            exit()

        for index in range(len(labmembers)):
            plot_whereabouts_ydata[index].append(int(whereabouts_dict[timestamp][index]) + 0.0)

    earliest_hour = int(plot_xdata[0]/1000/60/60)*1000*60*60
    latest_hour = (int(plot_xdata[-1]/1000/60/60) + 1)*1000*60*60

    for index in range(len(labmembers)):
        axarr[index].step(plot_xdata, plot_groundtruth_ydata[index], 'r-', where='post', label='Ground Truth')
        axarr[index].step(plot_xdata, plot_whereabouts_ydata[index], 'b--', where='post', label='Whereabouts')
        axarr[index].set_xbound(earliest_hour, latest_hour)
        axarr[index].set_xticks([i for i in range(earliest_hour, latest_hour, 1000*60*60)])
        axarr[index].set_ybound(-0.5, 1.5)
        axarr[index].set_yticks([0, 1])
        axarr[index].set_yticklabels(['Absent', 'Present'])

    axarr[0].legend(loc='best')
    #XXX: this is a kludge. All that work to stay data-anonymous, and then just do this...
    axarr[-1].set_xticklabels([i for i in range(9, 24)])

plt.show()
