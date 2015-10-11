#!/usr/bin/env python

import ast
import dataprint

scanner_mapping = {
            '1C:BA:8C:ED:ED:2A': ('University of Michigan|BBB|4908', '0'),
            '1C:BA:8C:9B:BC:57': ('University of Michigan|BBB|4901', '1'),
            'D0:5F:B8:FE:47:BB': ('University of Michigan|BBB|4670', '2'),
            'D0:39:72:30:71:3E': ('University of Michigan|BBB|4916', '3'),
            '1C:BA:8C:ED:E0:B2': ('University of Michigan|BBB|4776', '4'),
            '6C:EC:EB:9F:70:53': ('USA|Michigan|Ann Arbor|1929 Plymouth', '5')
            }

infile = open('gatd_extract.dat', 'r')
outfile = open('rssi_view.dat', 'w')

unique_packets = 0
occurances = [0, 0, 0, 0]
pkt_group = [{'time': -1000000}]
out_data = []
out_data.append(["#time", "4908", "4901", "4670", "4916", "4776", "1929"])

for line in infile:
    # read in as dict
    data = ast.literal_eval(line.replace('ObjectId', ''))
    data['location_str'] = scanner_mapping[data['scanner_macAddr']][0]
    data['location_id'] = scanner_mapping[data['scanner_macAddr']][1]

    #print(data['time'] - pkt_group[0]['time'])
    if (data['time'] - pkt_group[0]['time']) < 500:
        pkt_group.append(data)
    else:
        if len(pkt_group) > 1:
            occurances[len(pkt_group)-2] += 1

            group_data = [pkt_group[0]['time']] + [-200]*6
            for pkt in pkt_group:
                if group_data[int(pkt['location_id'])+1] != -200:
                    print("Error: duplicate data? " + str(pkt_group))
                    exit()

                group_data[int(pkt['location_id'])+1] = pkt['rssi']

            out_data.append(group_data)

        # pkt group should always include this point
        unique_packets += 1
        pkt_group = [data]


print("Unique packets:  " + str(unique_packets))
print("Double detected: " + str(occurances[0]))
print("Triple detected: " + str(occurances[1]))
print("Quad   detected: " + str(occurances[2]))
print("Quint  detected: " + str(occurances[3]))
print("")
print("Multiply detected: " + str(sum(occurances)/float(unique_packets)*100) + ' %')
dataprint.to_file(outfile, out_data)

outfile.close()


