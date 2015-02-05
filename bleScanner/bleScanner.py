#!/usr/bin/env python

import sys
import os
import time
import signal
import Queue
import json
import glob
import urllib2
import logging
import logging.handlers
import argparse
from threading import Thread
from bleAPI import Packet
from bleAPI import Exceptions

# recording scanner mac address for determining location automatically
import subprocess
command = "ifconfig eth0 | grep HWaddr | cut -dH -f2 | cut -d\  -f2"
MAC_ADDRESS = subprocess.check_output(command, shell=True)[0:-1].upper()

try:
    from serial import SerialException
    import serial.tools.list_ports
except ImportError:
    print('Could not import the pyserial library.')
    print('sudo pip install pyserial')
    sys.exit(1)

try:
    import socketIO_client as sioc
except ImportError:
    print('Could not import the socket.io client library.')
    print('sudo pip install socketIO-client')
    sys.exit(1)

USAGE ="""
Scans for bluetooth low-energy devices

To perform a one-time scan, enter:
    test

To perform continuous monitoring, please specify the location being monitored.
Locations should be specified in the format:
    University|Building|Room

The following locations have been seen historically:"""
LOCATION = ""

LOCAL_FILE = ""

PACKET_COUNT = 0
UNIQUE_COUNT = 0
START_TIME = time.time()

BLEADDR_PROFILE_ID = 'ySYH83QLG2'
BLEADDR_EXPLORE_ADDR = 'http://gatd.eecs.umich.edu:8085/explore/profile/' + BLEADDR_PROFILE_ID
BLEADDR_POST_ADDR = 'http://gatd.eecs.umich.edu:8081/' + BLEADDR_PROFILE_ID

KNOWN_DEVICES = {
        'ec:84:04:f4:4a:07': 'Neal Jackson',
        'e2:a7:7f:78:34:24': 'Alex Halderman',
        'f9:97:1e:8b:e7:27': 'Branden Ghena',
        'ee:b7:8c:0d:8d:4d': 'Brad Campbell',
        'e8:74:72:8f:e4:57': 'William Huang',
        'ca:a3:bb:ea:94:5b': 'Meghan Clark',
        'd1:c6:df:67:1c:60': 'Rohit Ramesh',
        'ca:2d:39:50:f0:b1': 'Pat Pannuto',
        'f0:76:0f:09:b8:63': 'Noah Klugman',
        'ec:6d:04:74:fa:69': 'Yihua Guo',
        'f4:bb:3c:af:99:6c': 'Ben Kempke',
        'db:eb:52:c7:90:74': 'Sam DeBruin',
        'f7:fd:9a:80:91:79': 'Genevieve Flaspohler',
        'cb:14:57:58:b4:89': 'Charlie Welch',
        'de:da:9c:f1:75:94': 'David Adrian',
        'cd:49:fa:6a:98:b1': 'Spare Blue Force',
        'ee:47:fa:fe:ac:c2': 'Eva Robert',
        'c4:26:da:a4:72:c3': 'Ye-Sheng Kuo',
        'f1:7c:98:6e:b9:d1': 'Jessica De Jong',
        'e0:5e:5a:28:85:e3': 'Thomas Zachariah',
        'ca:28:2b:08:f3:f7': 'Josh Adkins',
        'ef:b1:85:b1:37:d4': 'Taped Nordic Tag',
        'e8:2c:76:b7:f7:8f': "Noah's Nordic Tag",
        '70:ee:50:05:27:24': 'June UV'
        }

def main():
    global USAGE, LOCATION, LOCAL_FILE

    # argument parsing
    parser = argparse.ArgumentParser(description='Scan for bluetooth low-energy devices.')
    parser.add_argument('-local', '--local', help='Run script locally. Specify output file')
    args = parser.parse_args()

    if args.local:
        LOCAL_FILE = args.local

    # get a list of previously scanned locations
    #try:
    #    scan_locations = get_scan_locations()
    #except urllib2.URLError:
    #    print("Connection to inductor unavailable. Running in test mode")
    #    LOCATION = 'test'
    #else:
    #    # get location
    #    if len(sys.argv) != 2:
    #        print(USAGE)
    #        index = 0
    #        for location in scan_locations:
    #            print("\t[" + str(index) + "]: " + location)
    #            index += 1
    #        print("")
    #        user_input = raw_input("Select a location or enter a new one: ")

    #         if user_input == '':
    #             print("Invalid selection")
    #             sys.exit(1)

    #         if user_input.isdigit():
    #             user_input = int(user_input)
    #             if 0 <= user_input < index:
    #                 LOCATION = scan_locations[user_input]
    #             else:
    #                 print("Invalid selection")
    #                 sys.exit(1)
    #         else:
    #             LOCATION = user_input
    #     else:
    #         LOCATION = sys.argv[1]
    #XXX: for now location is set to 'demo' and updated in the formatter
    LOCATION = 'demo'

    # setup logging
    log = logging.getLogger('bleScanner_log')
    log.setLevel(logging.ERROR)
    log_filename = '../logs/bleScanner_log_' + str(LOCATION.split('|')[-1]) + '.out'
    handler = logging.handlers.TimedRotatingFileHandler(log_filename,
            when='midnight', backupCount=7)
    log.addHandler(handler)
    
    # print location to user
    if LOCATION == 'test':
        print('Running test scans...')
        log.info(curr_datetime() + "Running test scans... " + LOCATION)
    else:
        print('Running bleScanner at ' + LOCATION)
        log.info(curr_datetime() + "Running bleScanner at " + LOCATION)

    # create thread to handle posting to GATD
    msg_queue = None
    post_thread = None
    rate_limit = True
    if LOCATION != 'test':
        msg_queue = Queue.Queue()
        if LOCAL_FILE:
            post_thread = LocalPoster(msg_queue, log=log)
            rate_limit = False
        else:
            post_thread = GATDPoster(msg_queue, log=log)
            rate_limit = True

    # begin BLE scans, catch all exceptions and try to keep running
    scanner = BLEScanner(queue = msg_queue, thread=post_thread, log=log, rate_limit=rate_limit)
    while True:
        try:
            scanner.scan()
        except Exception as e:
            log.error(curr_datetime() + "ERROR - BLEScanner: " + str(e))


class BLEScanner():

    def __init__(self, log, queue=None, thread=None, sample_window=10, rate_limit=True):
        self.msg_queue = queue
        self.thread = thread
        self.log = log
        self.sample_window = sample_window
        self.rate_limit = rate_limit

        self.devices = {}
        self.last_packet = time.time()
        self.last_update = 0
        self.last_join = time.time()

        # find nrf51822 dongle
        self.port = self.find_port()
        if self.port == None:
            print("Couldn't find serial port")
            sys.exit(1)

        # create PacketReader
        self.reader = Packet.PacketReader(self.port)

    def find_port(self):
        #XXX: it would be nice if this worked on Mac too
        serial_ports = glob.glob('/dev/ttyACM*')
        if len(serial_ports) == 0:
            self.log.error(curr_datetime() + "ERROR - Couldn't find serial device")
            return None
        if len(serial_ports) > 1:
            self.log.info(curr_datetime() + "INFO - Multiple serial ports found")

        self.log.info(curr_datetime() + "INFO - Using serial port " + str(serial_ports[0]))
        return str(serial_ports[0])

    def scan(self):
        global PACKET_COUNT, UNIQUE_COUNT

        while True:
            packet_data = self._get_packet()
            if packet_data == None:
                continue

            [ble_addr, rssi, name, payload] = packet_data

            # create device if necessary
            if ble_addr not in self.devices:
                UNIQUE_COUNT += 1
                self.devices[ble_addr] = {}
                self.devices[ble_addr]['count'] = 0
                self.devices[ble_addr]['rssi'] = {'average': -200,
                        'newest': -200, 'samples': {}}
                self.devices[ble_addr]['timestamp'] = 0
                self.log.info(curr_datetime() + "INFO - BLE Device " +
                        str(ble_addr) + " first seen")

            # save various metadata about the connection
            current_time = time.time()
            PACKET_COUNT += 1
            self.last_packet = current_time
            dev = self.devices[ble_addr]
            dev['count'] += 1
            dev['name'] = name
            dev['rssi']['newest'] = rssi

            # save RSSI data. Only keep values from within the last sample window
            for timestamp in dev['rssi']['samples'].keys():
                if float(timestamp) < (current_time - self.sample_window):
                    del dev['rssi']['samples'][timestamp]
            dev['rssi']['samples'][current_time] = rssi
            dev['rssi']['average'] = self._median(dev['rssi']['samples'].values())

            # check if this packet should actually be sent to GATD. Rate limit
            #   to one per second
            if self.rate_limit and int(dev['timestamp']) >= int(current_time):
                continue
            dev['timestamp'] = current_time

            # push to message queue if it exists
            if self.msg_queue != None:
                # check if thread is still alive
                if self.thread and not self.thread.isAlive():
                    self.log.error(curr_datetime() + "ERROR - Post to GATD thread died!!")
                    sys.exit(1)

                # push data to thread to be posted
                self.msg_queue.put([ble_addr, dev, payload])

            # update screen
            self.update_screen()

            # wait on the darn GATD poster to catch up to real time
            if ((current_time - self.last_join) > 10):
                self.last_join = current_time
                self.msg_queue.join()

    def update_screen(self):
        global KNOWN_DEVICES

        # there are 52 usable lines in a fullsize terminal on my screen
        SCREEN_LINES = 52

        # only update once per second at most
        if (time.time() - self.last_update) > 1:
            self.last_update = time.time()

            # clear terminal screen
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Time: " + time.strftime("%I:%M:%S"))

            # print devices by RSSI with named devices always shown
            index = 0
            sorted_addrs = sorted(self.devices,
                    key=lambda ble_addr: self.devices[ble_addr]['rssi']['newest'],
                    reverse=True)
                    #key=lambda ble_addr: self.devices[ble_addr]['rssi']['average'],
            other_lines = SCREEN_LINES - len([x for x in sorted_addrs if x in KNOWN_DEVICES])

            for ble_addr in sorted_addrs:
                index += 1
                if other_lines > 0 or ble_addr in KNOWN_DEVICES:
                    # print all labeled devices and the top remaining devices that fit on screen
                    if ble_addr not in KNOWN_DEVICES:
                        other_lines -= 1
                    self._print_device(index, ble_addr)

    def _print_device(self, index, ble_addr):
        global KNOWN_DEVICES

        dev = self.devices[ble_addr]
        print_str = "(" + str(index) + ")" + \
                    "\tADDR: " + str(ble_addr) + \
                    "  RSSI: " + str(dev['rssi']['newest'])
                    #"  RSSI: " + str(dev['rssi']['average'])

        time_diff = int(round(time.time() - dev['timestamp']))
        print_str += "\tAgo: " + str(time_diff)
        if time_diff < 100:
            print_str += '  '

        if ble_addr in KNOWN_DEVICES:
            print_str += "\t" + str(KNOWN_DEVICES[ble_addr])
        else:
            print_str += "\t" + str(dev['name'])

        print(print_str)

    def _median(self, alist):
        # sort list and find middle
        srtd = sorted(alist)
        mid = len(alist)/2
        if len(alist) %2 == 0:
            # take the average of the middle two
            return int(round((srtd[mid-1] + srtd[mid]) / 2.0))
        else:
            # return the middle value
            return int(round(srtd[mid]))

    def _get_packet(self):
        try:
            packet = self.reader.getPacket(timeout = 2)
        except Exceptions.SnifferTimeout:
            return None
        except Exceptions.InvalidPacketException:
            return None
        except (SerialException, ValueError):
            self.log.error(curr_datetime() + "ERROR - UART read error")
            return None
        else:
            return self._process_packet(packet)

    def _process_packet(self, packet):
        EVENT_PACKET = 0x06
        if (packet.valid and packet.OK and packet.crcOK and
                packet.id == EVENT_PACKET and not packet.direction and
                packet.blePacket.advType in [0, 1, 2, 4, 6] and
                packet.blePacket.advAddress != None):
            ble_addr = "{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}".format(
                    packet.blePacket.advAddress[0],
                    packet.blePacket.advAddress[1],
                    packet.blePacket.advAddress[2],
                    packet.blePacket.advAddress[3],
                    packet.blePacket.advAddress[4],
                    packet.blePacket.advAddress[5])
            rssi = packet.RSSI
            # remove silly quotation marks
            name = packet.blePacket.name[1:-1]
            # add in advertisement payload
            payload = packet.blePacket.payload

            return [ble_addr, rssi, name, payload]
        else:
            return None

class GATDPoster(Thread):
    def __init__(self, queue, log=None):
        # init thread
        super(GATDPoster, self).__init__()
        self.daemon = True

        # init data
        self.msg_queue = queue
        self.log = log

        # autostart thread
        self.start()

    def run(self):
        global LOCATION, BLEADDR_POST_ADDR, MAC_ADDRESS

        while True:
            # look for a packet
            [ble_addr, dev, payload] = self.msg_queue.get()
            data = {
                    'location_str': LOCATION,
                    'ble_addr': ble_addr,
                    'rssi': dev['rssi']['newest'],
                    'avg_rssi': dev['rssi']['average'],
                    'name': dev['name'],
                    'scanner_macAddr': MAC_ADDRESS,
                    'payload': payload
                    }

            # post to GATD
            #XXX: Change this to do UDP posts instead of HTTP posts for speed
            try:
                req = urllib2.Request(BLEADDR_POST_ADDR)
                req.add_header('Content-Type', 'application/json')
                response = urllib2.urlopen(req, json.dumps(data))
            except Exception as e:
                # ignore error and carry on
                if self.log:
                    self.log.error(curr_datetime() + "ERROR - GATDPoster: " + str(e))
                else:
                    print(curr_datetime() + "ERROR - GATDPoster: " + str(e))
            finally:
                self.msg_queue.task_done()


class LocalPoster(Thread):
    def __init__(self, queue, log=None):
        global LOCAL_FILE

        # init thread
        super(LocalPoster, self).__init__()
        self.daemon = True

        # init data
        self.msg_queue = queue
        self.log = log

        # try to open file
        self.f = open(LOCAL_FILE, 'a+')

        # autostart thread
        self.start()

    def run(self):
        global LOCATION

        while True:
            # look for a packet
            [ble_addr, dev] = self.msg_queue.get()
            data = {
                    'time': dev['timestamp'],
                    'location_str': LOCATION,
                    'ble_addr': ble_addr,
                    'rssi': dev['rssi']['newest'],
                    'avg_rssi': dev['rssi']['average'],
                    'name': dev['name'],
                    'scanner_macAddr': MAC_ADDRESS
                    }

            # write to file
            self.f.write(str(json.dumps(data)) + "\n")

            self.msg_queue.task_done()

def curr_datetime():
    return time.strftime("%m/%d/%Y %H:%M:%S ")

def get_scan_locations():
    global BLEADDR_EXPLORE_ADDR

    # query GATD explorer to find scan locations
    req = urllib2.Request(BLEADDR_EXPLORE_ADDR)
    response = urllib2.urlopen(req)
    json_data = json.loads(response.read())

    if 'location_str' in json_data:
        return json_data['location_str'].keys()
    else:
        return ['None']

def sigint_handler(signum, frame):
    # exit the program if we get a CTRL-C
    global PACKET_COUNT, UNIQUE_COUNT, START_TIME

    print("\n")
    print("Unique Devices: " + str(UNIQUE_COUNT))
    print("Total Packets:  " + str(PACKET_COUNT))
    print("Uptime:         " + str(int(round(time.time() - START_TIME))) + " seconds")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, sigint_handler)
    main()

