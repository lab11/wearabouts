#!/usr/bin/env python

import sys
import ast
import dataprint

def main( ):
    scanner_mapping = {
                '1C:BA:8C:ED:ED:2A': ('University of Michigan|BBB|4908', '0'),
                '1C:BA:8C:9B:BC:57': ('University of Michigan|BBB|4901', '1'),
                'D0:5F:B8:FE:47:BB': ('University of Michigan|BBB|4670', '2'),
                'D0:39:72:30:71:3E': ('University of Michigan|BBB|4916', '3'),
                '1C:BA:8C:ED:E0:B2': ('University of Michigan|BBB|4776', '4'),
                '6C:EC:EB:9F:70:53': ('USA|Michigan|Ann Arbor|1929 Plymouth', '5')
                }

    if len(sys.argv) != 2:
        print("Missing input argument: GATD data file to parse")
        exit()

    infile = open(sys.argv[1], 'r')
    outfile = open('wearabouts_averaging.dat', 'w')

    out_data = []
    out_data.append(['#time', '4908', '4901', '4670', '4916', '4776'])

    # parse packets to generate wearabouts avg RSSI view for each room
    BLE_DURATION = 75*1000
    BLE_MINIMUM_COUNT = 12
    start_timestamp = 1441060063 * 1000
    presences = {}
    prev_state = [-200*5]
    curr_time = 0
    line_num = 0
    for line in infile:
        line_num += 1

        # read in as dict
        data = ast.literal_eval(line.replace('ObjectId', ''))
        data['location_str'] = scanner_mapping[data['scanner_macAddr']][0]
        data['location_id'] = scanner_mapping[data['scanner_macAddr']][1]

        pkt_time = data['time']
        pkt_loc  = data['location_id']
        pkt_rssi = data['rssi']

        # handle data decay that occurred since the last packet and before this packet
        while True:
            # find packet that should decay
            min_time = (pkt_time-BLE_DURATION) # packets older than this should decay
            min_loc = -1
            for loc in presences:
                if len(presences[loc]['times']) > 0 and presences[loc]['times'][0] < min_time:
                    min_time = presences[loc]['times'][0]
                    min_loc = loc
            if min_loc != -1:
                # there is a packet that should decay
                curr_time = min_time+BLE_DURATION # the time at which it actually decays
                presences[min_loc]['times'].pop(0)
                presences[min_loc]['rssis'].pop(0)

                # recalculate state
                curr_state = [-200]*5
                for loc in sorted(presences.keys()):
                    if len(presences[loc]['rssis']) > BLE_MINIMUM_COUNT:
                        avg_rssi = sum(presences[loc]['rssis'])/len(presences[loc]['rssis'])
                        curr_state[int(loc)] = avg_rssi
                    else:
                        curr_state[int(loc)] = -200

                # record state change
                if curr_state != prev_state:
                    out_data.append([curr_time/1000]+curr_state)
                prev_state = curr_state
            else:
                break

        # we are caught up to all decays before this packet. Handle the packet
        if pkt_loc not in presences:
            presences[pkt_loc] = {
                    'times': [],
                    'rssis': [],
                    }
        presences[pkt_loc]['times'].append(pkt_time)
        presences[pkt_loc]['rssis'].append(pkt_rssi)

        # recalculate state
        curr_time = pkt_time
        curr_state = [-200]*5
        for loc in sorted(presences.keys()):
            if len(presences[loc]['rssis']) > BLE_MINIMUM_COUNT:
                avg_rssi = sum(presences[loc]['rssis'])/len(presences[loc]['rssis'])
                curr_state[int(loc)] = avg_rssi
            else:
                curr_state[int(loc)] = -200

        # record state change
        if curr_state != prev_state:
            out_data.append([curr_time/1000]+curr_state)
        prev_state = curr_state


    # eliminate all avg RSSI data that is not a state change in at least one room we care about
    #TODO

    dataprint.to_file(outfile, out_data)

    infile.close()
    outfile.close()


if __name__=="__main__":
    main()

