#!/usr/bin/env python3

prev_time = 0
times = []
with open('300sec_scan.dat', 'r') as f:
    for line in f:
        # skip headers
        if line[0] == '#':
            continue

        # get data fields
        line_data = line.split()
        time = float(line_data[0])
        rssi = line_data[1]

        if prev_time == 0:
            prev_time = time
            continue

        times.append(round(time-prev_time, 3))
        prev_time = time


range_data = [x*0.001 for x in range(0, 2000, 1)]
pdf_data = dict(zip(range_data, [0]*len(range_data)))
counts = 0
for time in times:
    if time not in range_data:
        continue

    pdf_data[time] += 1
    counts += 1

with open('300sec_scan_pdf.dat', 'w') as f:
    f.write('# probability distribution for 300 second fitbit scan\n')

    for time in sorted(pdf_data):
        prob = float(pdf_data[time]/float(counts))
        f.write(str(round(time, 3)) + '\t' + str(prob) + '\n')

