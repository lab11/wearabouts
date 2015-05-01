#!/usr/bin/env python2

import IPy
import json
import sys
from threading import Thread
import Queue
import time
import random
import os
import urllib2
import pika
import argparse

import logging
import logging.handlers

try:
    import socketIO_client as sioc
except ImportError:
    print('Could not import the socket.io client library.')
    print('sudo pip install socketIO-client')
    sys.exit(1)

try:
    import dataprint
except ImportError:
    print('Could not import the dataprint library.')
    print('sudo pip install dataprint')
    sys.exit(1)

def main( ):

    # setup logging
    log = logging.getLogger('forwarder_log')
    log.setLevel(logging.DEBUG)
    log_filename = '../../logs/experimental_analyzer.out'
    handler = logging.handlers.TimedRotatingFileHandler(log_filename,
            when='midnight', backupCount=7)
    log.addHandler(handler)
    log.info("Running RSSI analyzer...")
    print("Running RSSI analyzer...")

    # check for inputs. Defaults to search for Branden's fitbit
    target_ble_addr = 'f9:97:1e:8b:e7:27'
    if len(sys.argv) == 2:
        target_ble_addr = sys.argv[1]

    # start threads to receive data from RabbitMQ
    threads = []
    bleAddr_queue = Queue.Queue()
    threads.append(RabbitMQReceiverThread('experimental.scanner.bleScanner.#', 'bleAddr', bleAddr_queue, log))
    #wearabouts_queue = Queue.Queue()
    #threads.append(RabbitMQReceiverThread('experimental.wearabouts.#', 'wearabouts', wearabouts_queue, log))

    # open a file for data output
    dat_file = open('data_rssi.dat', 'w')
    dat_file.write('#')
    dataprint.to_file(dat_file, [['time', 'rssi', 'location id', 'location name']])

    # print data to user every second
    last_print_time = 0
    num_packets = 0
    start_time = time.time()
    dat_file.write('# Start time = ' + str(start_time) + '\n')

    old_num_packets = -1

    while True:

        data_type = 'None'
        pkt = None
        try:
            # wait for data to arrive
            [data_type, pkt] = bleAddr_queue.get(timeout=5)
        except Queue.Empty:
            # No data has been seen, timeout

            # check if the receive thread is still alive
            for thread in threads:
                if thread and not thread.isAlive():
                    log.error(curr_datetime() + "ERROR - thread died")
                    sys.exit(1)

        # print status to user
        #if (time.time() - last_print_time) > 1:
        if (num_packets%100) == 0 and num_packets != old_num_packets:
            old_num_packets = num_packets
            last_print_time = time.time()
            print(str(time.time() - start_time) + ' - Number of packets: ' + str(num_packets))
        
        # get uniqnames and location ids
        pkt = apply_mappings(pkt)

        # check data for validity
        if (pkt == None or 'location_str' not in pkt or 'time' not in pkt or
                'ble_addr' not in pkt or 'location_id' not in pkt):
            continue

        # only save packets that correspond to the measured rooms
        if pkt['location_str'].split('|')[-1] not in ['4908', '4901', '4670', '4916', '4776']:
            continue

        # only save packets that correspond to real people
        if 'uniqname' not in pkt:
            continue

        # check for a specific BLE address
        #print(pkt['ble_addr'])
        #if pkt['ble_addr'] != target_ble_addr:
        #    continue

        # print data to file

        num_packets += 1
        data = [[pkt['time']-start_time, pkt['ble_addr'], pkt['rssi'], pkt['location_id'], pkt['location_str'].split('|')[-1]]]
        dataprint.to_file(dat_file, data)

scanner_mapping = {
        '1C:BA:8C:ED:ED:2A': ('University of Michigan|BBB|4908', '0'),
        '1C:BA:8C:9B:BC:57': ('University of Michigan|BBB|4901', '1'),
        'D0:39:72:4B:AD:14': ('University of Michigan|BBB|4670', '2'),
        '6C:EC:EB:A5:98:E2': ('University of Michigan|BBB|4916', '3'),
        '1C:BA:8C:ED:E0:B2': ('University of Michigan|BBB|4776', '4'),
        '6C:EC:EB:9F:70:53': ('USA|Michigan|Ann Arbor|1929 Plymouth', '5')
        }

people_mapping = {
        'ec:84:04:f4:4a:07': ('nealjack', 'Neal Jackson'),
        'e2:a7:7f:78:34:24': ('jhalderm', 'Alex Halderman'),
        'f9:97:1e:8b:e7:27': ('brghena', 'Branden Ghena'),
        'ee:b7:8c:0d:8d:4d': ('bradjc', 'Brad Campbell'),
        'e8:74:72:8f:e4:57': ('wwhuang', 'William Huang'),
        'ca:a3:bb:ea:94:5b': ('mclarkk', 'Meghan Clark'),
        'd1:c6:df:67:1c:60': ('rohitram', 'Rohit Ramesh'),
        'f0:76:0f:09:b8:63': ('nklugman', 'Noah Klugman'),
        'ec:6d:04:74:fa:69': ('yhguo', 'Yihua Guo'),
        'f4:bb:3c:af:99:6c': ('bpkempke', 'Ben Kempke'),
        'db:eb:52:c7:90:74': ('sdebruin', 'Sam DeBruin'),
        'f7:fd:9a:80:91:79': ('genevee', 'Genevieve Flaspohler'),
        'dc:fa:65:c7:cd:34': ('cfwelch', 'Charlie Welch'),
        'de:da:9c:f1:75:94': ('davadria', 'David Adrian'),
        'cd:49:fa:6a:98:b1': ('None', 'Spare Blue Force'),
        'ca:2d:39:50:f0:b1': ('ppannuto', 'Pat Pannuto'),
        'ee:47:fa:fe:ac:c2': ('evrobert', 'Eva Robert'),
        'c4:26:da:a4:72:c3': ('samkuo', 'Ye-Sheng Kuo'),
        'f1:7c:98:6e:b9:d1': ('jdejong', 'Jessica De Jong'),
        'e0:5e:5a:28:85:e3': ('tzachari', 'Thomas Zachariah'),
        'ca:28:2b:08:f3:f7': ('adkinsjd', 'Josh Adkins'),
        'fa:38:b5:a6:fe:6e': ('sarparis', 'Sarah Paris'),
        }

def apply_mappings(pkt):
    if pkt == None:
        return

    # location parsing
    if 'location_str' in pkt and (pkt['location_str'] == 'demo' or pkt['location_str'] == 'unknown'):
        # find the location string
        if 'scanner_macAddr' in pkt and pkt['scanner_macAddr'] in scanner_mapping:
            pkt['location_str'] = scanner_mapping[pkt['scanner_macAddr']][0]
            pkt['location_id'] = scanner_mapping[pkt['scanner_macAddr']][1]
        else:
            pkt['location_str'] = 'unknown'
            pkt['location_id'] = -1

    # add people identities
    if 'ble_addr' in pkt and pkt['ble_addr'] in people_mapping:
        pkt['uniqname'] = people_mapping[pkt['ble_addr']][0]
        pkt['full_name'] = people_mapping[pkt['ble_addr']][1]

    # return updated packet
    return pkt

def curr_datetime():
    return time.strftime("%m/%d/%Y %H:%M:%S ")


class RabbitMQReceiverThread (Thread):

    def __init__(self, route_key, data_type, message_queue, log):
        # init thread
        super(RabbitMQReceiverThread, self).__init__()
        self.daemon = True

        # init data
        self.route_key = route_key
        self.data_type = data_type
        self.message_queue = message_queue
        self.log = log

        self.recv_count = 0

        # start thread
        print("Running thread")
        self.start()


    def run(self):
        try:
            import config
        except ImportError:
            print('Cannot find config file. Need symlink from shed')
            sys.exit(1)

        while True:
            try:
                amqp_conn = pika.BlockingConnection(
                        pika.ConnectionParameters(
                            host = config.rabbitmq['host'],
                            virtual_host=config.rabbitmq['vhost'],
                            credentials=pika.PlainCredentials(
                                config.rabbitmq['login'],
                                config.rabbitmq['password'])))

                amqp_chan = amqp_conn.channel()

                result = amqp_chan.queue_declare(exclusive=True)

                queue_name = result.method.queue
                amqp_chan.queue_bind(
                        exchange=config.rabbitmq['exchange'],
                        queue = queue_name,
                        routing_key = self.route_key)

                amqp_chan.basic_consume(self._on_data, queue_name, no_ack=True)

                amqp_chan.start_consuming()
            except Exception as e:
                self.log.error(curr_datetime() + "ERROR - RabbitMQReceiver: " + str(e) + repr(e))

    def _on_data(self, channel, method, prop, body):
        # data received from rabbitmq. Push to msg_queue
        self.message_queue.put([self.data_type, json.loads(body)])


if __name__=="__main__":
    main()

