#!/usr/bin/env python3

import json
import sys
import os
import ast
import math
import dataprint

# parameters
num_hours = 27
num_heros = 74
start_unix_time = 1414602000000

# get input file
infile = 'terraswarm_presenceData'
print("Processing file " + str(infile))

# store data in different format
print("parsing file")
locations = {}
heros = {}
init_pkt = True
start_time = start_unix_time
pkt_index = 0
with open(infile) as f:
    for line in f:
        try:
            pkt = ast.literal_eval(line)
        except Exception as e:
            print("ERROR: " + str(e))
            print(str(line))
            sys.exit(1)

        if init_pkt:
            init_pkt = False
            #start_time = pkt['time']

        uniqname = pkt['uniqname']
        time = (pkt['time'] - start_time)
        location_id = int(pkt['location_id'])
        present_by = pkt['present_by']
        
        if location_id not in locations:
            location_str = pkt['location_str']
            locations[location_id] = location_str

        data_tuple = (time, location_id)
        if uniqname not in heros:
            heros[uniqname] = []
        else:
            # don't add redundant data points
            if heros[uniqname][-1][1] == location_id:
                continue
        heros[uniqname].append(data_tuple)

        # only keep going until two days are complete
        pkt_index += 1
        if time > 172800000:
            print("ran over time at packet " + str(pkt_index))
            break

# assign colors to locations
loc_color = {}
colors = ['"#2eaa4a"', '"#026699"', '"#a91e23"', '"#ffc74e"', '"#6a624d"']
for location_id in locations:
    if location_id == -1:
        loc_color[location_id] = '"#ffffff"'
    else:
        loc_color[location_id] = colors[int(location_id)]

# create tics command
tics = '('
for hour in range(num_hours):
    time = '"' + str((hour+11)%12) + ':00" '
    if time == '"0:00" ':
        time = '"12:00" '
    loc = str(hour*3600*1000)
    tics += time + loc + ', '

tics = tics[0:-2] + ')'

# open gnuplot file and create initial commands
print("generating gnuplot file")
f = open('terraswarm_graph.gnuplot', 'w')
initial_commands = '''set terminal postscript enhanced eps color font "Helvetica,14" size 10.5in,8in
set output "terraswarm_graph.eps"

set style line 1 lt 1  ps 1.5 pt 7 lw 5 lc rgb "#d7191c"
set style line 2 lt 1  ps 1.2 pt 2 lw 5 lc rgb "#fdae61"
set style line 3 lt 1  ps 1.2 pt 3 lw 5 lc rgb "#abdda4"
set style line 4 lt 1  ps 0.5 pt 7 lw 5 lc rgb "#2b83ba"
set style line 5 lt 3  ps 1.2 pt 7 lw 3 lc rgb "#000000"

set border 3
'''
f.write(initial_commands)

f.write('set xlabel "Time (s)"\n')
#f.write('set xdata time\n')
#f.write('set timefmt "%H"\n')
f.write('set xtics 3600000 nomirror' + str(tics) + '\n')
f.write('set xrange [' + str(0) + ':' + str(num_hours*3600*1000) + ']\n\n')

f.write('set ylabel "Tag ID"\n')
f.write('set ytics nomirror\n')
f.write('set yrange [0:' + str(num_heros+1) + ']\n')

f.write('unset key\n')
f.write('\n\n')


# create gnuplot commands for each id
index = 0
offset = 0.3
for uniqname in sorted(heros.keys()):
    index += 1
    f.write("# data for  (" + str(index) + ")" + str(uniqname) + "\n")
    print("data for  (" + str(index) + ")" + str(uniqname) + ('\t' if (len(uniqname) < 10) else '') + "\t\t" + str(len(heros[uniqname])) + " data points")

    prev_data = heros[uniqname][0]
    for data in heros[uniqname][1:]:
        command = "set object rect from "
        command += str(prev_data[0]) + ',' + str(index-offset) + ' to ' + str(data[0]) + ',' + str(index+offset)
        command += " fc rgb " + str(loc_color[prev_data[1]]) + " fs noborder"
        command += "\n"
        f.write(command)

        if data[0] > num_hours*3600*1000:
            break
        prev_data = data

    f.write("\n")

    if index == num_heros:
        break

# complete gnuplot file
f.write("# plot the boxes\n")
f.write("plot NaN\n")
f.close()

# finished! Print location ids for user
print("Complete!\n")
for location_id in sorted(locations.keys()):
    print(str(location_id) + ': ' + str(locations[location_id]) + ' - ' + str(loc_color[location_id]))

