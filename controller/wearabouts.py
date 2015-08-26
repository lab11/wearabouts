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
import traceback

try:
    import socketIO_client as sioc
except ImportError:
    print('Could not import the socket.io client library.')
    print('sudo pip install socketIO-client')
    sys.exit(1)

import logging
import logging.handlers

BLEADDR_PROFILE_ID = 'ySYH83QLG2'
WEARABOUTS_PROFILE_ID = '62MTxDGPhJ'
DOOR_PROFILE_ID = 'U8H29zqH0i'
MACADDR_PROFILE_ID = 'PGMR22B9wP'

BLEADDR_EXPLORE_ADDR = 'http://gatd.eecs.umich.edu:8085/explore/profile/' + BLEADDR_PROFILE_ID
WEARABOUTS_POST_ADDR = 'http://gatd.eecs.umich.edu:8081/' + WEARABOUTS_PROFILE_ID

def main( ):

    # argument parsing
    parser = argparse.ArgumentParser(description='Determine locations of individuals based on BLE scan information.')
    parser.add_argument('-rabbit', '--rabbit',
            help='Pipe data from and results to a RabbitMQ instance. Specified in config.py', action='store_true')
    args = parser.parse_args()

    USE_RABBITMQ = False
    if args.rabbit:
        USE_RABBITMQ = True

    # setup logging
    log = logging.getLogger('wearabouts_log')
    log.setLevel(logging.DEBUG)
    log_filename = '../logs/experimental_wearabouts_log.out'
    handler = logging.handlers.TimedRotatingFileHandler(log_filename,
            when='midnight', backupCount=7)
    log.addHandler(handler)
    log.info("Running wearabouts controller...")
    print("Running wearabouts controller...")

    # start threads to receive data from GATD or RabbitMQ
    recv_queue = Queue.Queue()
    post_queue = Queue.Queue()
    threads = []
    if USE_RABBITMQ:
        threads.append(RabbitMQReceiverThread('experimental.scanner.#', 'bleAddr', recv_queue, log))
        threads.append(RabbitMQPoster('experimental.wearabouts', post_queue, log=log))
    else:
        threads.append(SocketIOReceiverThread(BLEADDR_PROFILE_ID, {}, 'bleAddr', recv_queue))
        #TODO: Reactivate these once they are written
        #SocketIOReceiverThread(DOOR_PROFILE_ID,    {}, 'door',    message_queue)
        #SocketIOReceiverThread(MACADDR_PROFILE_ID, {}, 'macAddr', message_queue)
        threads.append(GATDPoster(WEARABOUTS_POST_ADDR, post_queue, log=log))

    # start presence controller
    controller = PresenceController(recv_queue, post_queue, threads, log)
    while True:
        try:
            controller.monitor()
        except Exception as e:
            log.error(curr_datetime() + "ERROR - PresenceController: " + str(e) + repr(e))
            log.error(traceback.format_exc())

def curr_datetime():
    return time.strftime("%m/%d/%Y %H:%M:%S ")


class PresenceController ():
    # how often locate should be run on everyone, seconds
    LOCATE_PERIOD = 10

    # how long to keep assuming someone is in the same room, seconds
    #   for now I am turning this off. Applications can do their own hysteresis
    #   if they so desire
    HYSTERESIS = 0

    # how long before a BLE sample is invalid, seconds
    BLE_DURATION = 75

    # how many BLE samples are necessary before an estimate is made
    BLE_MINIMUM_COUNT = 12

    # minimum BLE RSSI that counts as in the room, dBm
    BLE_MIN_RSSI = -150

    # how long to maintain a person in the dict with no further information
    PRESENCE_LIFETIME = 12*60*60

    def __init__(self, recv_queue, post_queue, threads, log):
        self.recv_queue = recv_queue
        self.post_queue = post_queue
        self.threads = threads
        self.log = log

        self.presences = {}
        self.locations = []
        self.last_locate_time = 0
        self.last_update = 0
        self.last_packet = 0
        self.start_time = time.time()

        self.last_gatd_post = {}

    def monitor(self):
        while True:

            data_type = 'None'
            pkt = None
            try:
                # wait for data from GATD
                [data_type, pkt] = self.recv_queue.get(timeout=self.LOCATE_PERIOD)
            except Queue.Empty:
                # No data has been seen, timeout to update presences
                pass

            self.update_screen()

            # check that input/output threads have not died
            for thread in self.threads:
                if thread and not thread.isAlive():
                    self.log.error(curr_datetime() + "ERROR - I/O thread died")
                    sys.exit(1)

            # automatically re-run locate if it's been static too long
            if ((time.time() - self.last_locate_time) > self.LOCATE_PERIOD):
                self.locate_everyone()

            # append fields to packet
            #   this may duplicate the GATD formatter if it is being used
            pkt = self.apply_mappings(pkt)

            # check data for validity
            if (pkt == None or 'location_str' not in pkt or 'time' not in pkt or
                    'uniqname' not in pkt or 'location_id' not in pkt):
                continue
            if ('full_name' not in pkt):
                # there should never be a uniqname but not a full_name, but if
                #   it does happen, I want the error logged
                self.log.error(curr_datetime() + 
                        "ERROR - No full_name in packet " + str(pkt))
                pkt['full_name'] = pkt['uniqname']

            # packet is definitely valid
            self.last_packet = time.time()

            # create person if necessary
            uniqname = pkt['uniqname']
            if uniqname not in self.presences:
                self.presences[uniqname] = {
                        'full_name': pkt['full_name'],
                        'location': 'None',
                        'location_id': -1,
                        'present_since': 0,
                        'last_seen': 0,
                        'last_packet_time': 0,
                        'confidence': 0,
                        'location_data': {}}
                self.last_gatd_post[uniqname] = 0
            person = self.presences[uniqname]

            # create location if necessary
            location = pkt['location_str']
            if location not in self.locations and location != 'None' and location != 'unknown':
                self.locations.append(location)
            if location not in person['location_data']:
                person['location_data'][location] = {
                        'last_seen': 0,
                        'location_id': pkt['location_id'],
                        'potentially_present': False,
                        'present_by': 'None'}
            evidence = person['location_data'][location]
            person['last_packet_time'] = time.time()

            # handle bleAddr data
            if data_type == 'bleAddr':
                # specific field validity testing
                if 'rssi' not in pkt or 'scanner_macAddr' not in pkt:
                    self.log.error(curr_datetime() + " Got an invalid ble packet")
                    continue

                # create dict if necessary
                if 'bleAddr' not in evidence:
                    evidence['bleAddr'] = {}

                # multiple scanners can exist at a single location
                scanner = pkt['scanner_macAddr']
                if scanner not in evidence['bleAddr']:
                    evidence['bleAddr'][scanner] = {
                            'avg_rssi': -200,
                            'times': [],
                            'rssis': []
                            }

                # update user information
                timestamp = int(round(pkt['time']))
                evidence['bleAddr'][scanner]['times'].append(timestamp)
                evidence['bleAddr'][scanner]['rssis'].append(pkt['rssi'])

                # locate the user based on this new information. Only relocate
                #   if the person may have entered or left, which is noted by
                #   a mismatch in determine_presence and in_location
                # Note: this isn't exactly perfect. It could fail if the user
                #   is really close to being in two locations (defaults to
                #   keeping the user in the same location). But, we are
                #   re-running locate_everyone() pretty often anyways, so this
                #   is really just here as a heuristic to speed up locating
                if (self.determine_presence(uniqname, location) != self.in_location(uniqname, location)):
                    self.locate_person(uniqname)

            #TODO: handle macAddr data
            #if data_type == 'macAddr':
            #    # specific field validity testing
            #    if 'avg_rssi' not in pkt:
            #        continue

            #    # create dict if necessary
            #    if 'macAddr' not in evidence:
            #        evidence['macAddr'] = {
            #                'time': 0,
            #                'rssi': -200,
            #                'address': ''
            #                }

            #    # update user information
            #    timestamp = int(round(pkt['time']/1000))
            #    if timestamp > evidence['macAddr']['time']:
            #        evidence['macAddr']['time'] = timestamp
            #        evidence['macAddr']['rssi'] = pkt['avg_rssi']
            #        evidence['macAddr']['address'] = pkt['mac_addr']

            #TODO: handle door event data
            #if data_type == 'door':
            #    # specific field validity testing
            #    if 'type' not in pkt:
            #        self.log.error(curr_datetime() +
            #                "ERROR - No type in door packet " + str(pkt))
            #        continue

            #    # create door events if necessary
            #    if 'door' not in evidence:
            #        evidence['door'] = {
            #                'time': 0,
            #                'open_count': 0
            #                }

            #    # update entry on rfid event
            #    if pkt['type'] == 'rfid':
            #        pkt_time = int(round(pkt['time']/1000))
            #        if pkt_time > evidence['door']['time']:
            #            evidence['door']['time'] = pkt_time
            #            evidence['door']['open_count'] = 0

            #    # update entry on door open event
            #    if pkt['type'] == 'door_open':
            #        for 

    scanner_mapping = {
            '1C:BA:8C:ED:ED:2A': ('University of Michigan|BBB|4908', '0'),
            '1C:BA:8C:9B:BC:57': ('University of Michigan|BBB|4901', '1'),
            #'D0:39:72:4B:AD:14': ('University of Michigan|BBB|4670', '2'),
            'D0:5F:B8:FE:47:BB': ('University of Michigan|BBB|4670', '2'),
            #'6C:EC:EB:A5:98:E2': ('University of Michigan|BBB|4916', '3'),
            'D0:39:72:30:71:3E': ('University of Michigan|BBB|4916', '3'),
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
            'c8:ee:59:3a:a0:16': ('azhen', 'Alan Zhen'),
            'dd:b3:e2:6d:92:2b': ('ppannuto_hr', 'Pat Pannuto HR'),
            }

    def apply_mappings(self, pkt):
        if pkt == None:
            return

        # location parsing
        if 'location_str' in pkt and (pkt['location_str'] == 'demo' or pkt['location_str'] == 'unknown'):
            # find the location string
            if 'scanner_macAddr' in pkt and pkt['scanner_macAddr'] in self.scanner_mapping:
                pkt['location_str'] = self.scanner_mapping[pkt['scanner_macAddr']][0]
                pkt['location_id'] = self.scanner_mapping[pkt['scanner_macAddr']][1]
            else:
                pkt['location_str'] = 'unknown'
                pkt['location_id'] = -1

        # add people identities
        if 'ble_addr' in pkt and pkt['ble_addr'] in self.people_mapping:
            pkt['uniqname'] = self.people_mapping[pkt['ble_addr']][0]
            pkt['full_name'] = self.people_mapping[pkt['ble_addr']][1]

        # return updated packet
        return pkt

    def update_screen(self):
        SCREEN_LINES = 58

        # only update once per second at most

        if (time.time() - self.last_update) > 1:
            self.last_update = time.time()
            
            # clear terminal screen
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Time: " + time.strftime("%I:%M:%S") +
                    '\t\t\tLast packet ' + str(int(round(time.time() - self.last_packet))) + 
                    ' seconds ago' +
                    '\t\tStarted ' + str(int(round(time.time() - self.start_time))) +
                    ' seconds ago')

            # print devices by uniqname
            sorted_uniqnames = sorted(self.presences.keys())

            index = 0
            for uniqname in sorted_uniqnames:
                index += 1
                self._print_person(index, uniqname)
                if index == SCREEN_LINES:
                    break

    def _print_person(self, index, uniqname):
        person = self.presences[uniqname]
        curr_loc = person['location']

        # print person header
        print_str = "(" + str(index) + ")" + \
                "\tName: " + str(person['full_name']) + \
                ('\t' if len(person['full_name']) > 9 else '\t\t') + \
                "Loc: " + str(curr_loc.split('|')[-1]) + '\n'

        # display data for each location
        for location in sorted(person['location_data'].keys()):
            for scanner in sorted(person['location_data'][location]['bleAddr'].keys()):
                data = person['location_data'][location]['bleAddr'][scanner]

                avg_rssi = data['avg_rssi']
                if avg_rssi == -200:
                    avg_rssi = '--'

                num_packets = len(data['times'])
                last_packet_ago = '--'
                if num_packets > 0:
                    last_packet_ago = int(round(time.time()-data['times'][-1]))

                loc_str = str(location.split('|')[-1][0:4]) + '-' + str(scanner)

                print_str += '\t' + loc_str + \
                        "\tAvg RSSI: " + str(avg_rssi) + \
                        "\tNum Packets: " + str(num_packets) + \
                        "\tAgo: " + str(last_packet_ago) + '\n'

        # actually print the data
        #   skips the last newline
        print(print_str[:-1])

    def in_location(self, uniqname, location):
        if (uniqname in self.presences):
            return (self.presences[uniqname]['location'] == location)

    def log_status(self, uniqname, location, present_by):
        if present_by != 'None':
            self.log.debug(curr_datetime() + "DEBUG - " + str(uniqname) +
                    " at " + str(location) + " present by " + str(present_by) +
                    ": " + str(self.presences[uniqname]))
        else:
            self.log.debug(curr_datetime() + "DEBUG - " + str(uniqname) + 
                    " at " + str(location) + " not present" +
                    ": " + str(self.presences[uniqname]))

    def present_by(self, data_type, uniqname, location):
        if (location == 'None'):
            if (data_type == 'None'):
                return True
            else:
                return False
        else:
            return (data_type ==
                    self.presences[uniqname]['location_data'][location]['present_by'])

    # some function to go through each person and figure out where they are
    def locate_everyone(self):
        self.last_locate_time = time.time()

        # find all the people
        locs = {}
        for uniqname in self.presences.keys():
            # also posts data to GATD for that uniqname
            loc = self.locate_person(uniqname)
            if loc == 'None':
                continue

            # keep track of each location that has people in it
            if loc not in locs:
                locs[loc] = {}
                locs[loc]['type'] = 'room'
                locs[loc]['location_str'] = loc
                locs[loc]['person_list'] = []
                locs[loc]['since_list'] = []

            # add uniqname to list of people in that room
            locs[loc]['person_list'].append({uniqname: self.presences[uniqname]['full_name']})
            if uniqname in self.presences:
                locs[loc]['since_list'].append({uniqname: self.presences[uniqname]['present_since']})
            else:
                self.log.error(curr_datetime() + "ERROR - Someone deleted when in a valid location? " + str(uniqname))
                locs[loc]['since_list'].append({uniqname: time.time()})

        # post each location in addtion to each individual
        empty_loc = {}
        empty_loc['type'] = 'room'
        empty_loc['location_str'] = 'None'
        empty_loc['person_list'] = []
        empty_loc['since_list'] = []
        for location in self.locations:
            if location in locs:
                # location is occupied
                self.post_queue.put((locs[location], location))
            else:
                # location is unoccupied
                empty_loc['location_str'] = location
                self.post_queue.put((empty_loc.copy(), location))

    # some function to go through each location in a person and figure out where they are
    #   also posts if there is a change
    def locate_person(self, uniqname):
        if uniqname in self.presences:
            person = self.presences[uniqname]
            possible_locations = []
            for location in person['location_data']:
                if (self.determine_presence(uniqname, location)):
                    possible_locations.append(location)

            curr_location = person['location']

            # check if the person is nowhere
            if (len(possible_locations) == 0):
                self.set_location(uniqname, 'None', 0.9)
                # remove the person from presences if not seen in a while
                if (time.time() - person['last_packet_time']) > self.PRESENCE_LIFETIME:
                    self.log.info(curr_datetime() + "INFO - Deleted " + uniqname)
                    del self.presences[uniqname]
                return 'None'

            # try choosing the best based on BLE
            ble_locs = [location for location in possible_locations
                    if (self.present_by('bleAddr', uniqname, location))]
            if (len(ble_locs) != 0):

                # get the highest average rssi and all locations with that value
                best_rssi = -200
                for loc in possible_locations:
                    for scanner in person['location_data'][loc]['bleAddr']:
                        if person['location_data'][loc]['bleAddr'][scanner]['avg_rssi'] > best_rssi:
                            best_rssi = person['location_data'][loc]['bleAddr'][scanner]['avg_rssi']
                best_locs = []
                for loc in possible_locations:
                    for scanner in person['location_data'][loc]['bleAddr']:
                        if person['location_data'][loc]['bleAddr'][scanner]['avg_rssi'] == best_rssi:
                            best_locs.append(loc)
                            break

                # pick from best locations
                new_location = 'None'
                confidence = 0
                if curr_location in best_locs:
                    # maintain the current location
                    new_location = curr_location
                    confidence = (1 - (-best_rssi)/101.0)
                else:
                    # find most scanner with most recently received packet
                    #   this breaks ties by selecting the last in order of [ble_locs]
                    most_recent = 0
                    most_recent_loc = 'None'
                    for loc in best_locs:
                        for scanner in person['location_data'][loc]['bleAddr']:
                            # ensure that this scanner is one of the best_locs
                            if (person['location_data'][loc]['bleAddr'][scanner]['avg_rssi'] == best_rssi and
                                    max(person['location_data'][loc]['bleAddr'][scanner]['times']) > most_recent):
                                most_recent = max(person['location_data'][loc]['bleAddr'][scanner]['times'])
                                most_recent_loc = loc
                    new_location = most_recent_loc
                    confidence = (1 - (-best_rssi)/101.0)

                # update the current location
                self.set_location(uniqname, new_location, confidence)
                return new_location

            #TODO: try choosing the best based on MAC

            #TODO: try choosing the best based on Door

            # the user is somewhere, but is not there by something we checked
            #   for. They are almost certainly just somewhere by time
            if curr_location in possible_locations:
                # persist the current location
                new_location = curr_location
                self.set_location(uniqname, new_location, 0.2)
                return new_location
            else:
                # why are we possibly here???
                self.log.error(curr_datetime() + "ERROR - Had to choose randomly")
                new_location = random.choice(possible_locations)
                self.set_location(uniqname, new_location, 0.001)
                return new_location

    def set_location(self, uniqname, location, confidence):
        curr_time = time.time()
        person = self.presences[uniqname]
        curr_location = person['location']

        person['confidence'] = max(confidence, 0)

        if (location != curr_location):
            person['location'] = location
            person['present_since'] = curr_time
            if location != 'None':
                person['location_id'] = person['location_data'][location]['location_id']
            else:
                person['location_id'] = -1

        present_by = 'None'
        if location != 'None':
            present_by = person['location_data'][location]['present_by']

        # this could be rate-limited
        post_data = True
        #post_data = False
        #if ((curr_time-self.last_gatd_post[uniqname]) > 20):
        #    post_data = True
        #    self.last_gatd_post[uniqname] = curr_time

        # post to GATD
        if post_data:
            data = {'type': 'person',
                    'uniqname': uniqname,
                    'full_name': person['full_name'],
                    'location_str': person['location'],
                    'location_id': person['location_id'],
                    'present_since': person['present_since'],
                    'last_seen': person['last_seen'],
                    'confidence': person['confidence'],
                    'present_by': present_by}
            self.post_queue.put((data, person['location']))

        #self.log_status(uniqname, location, present_by)

    # some function to go through a single location in a person and figure out if they could be in it
    def determine_presence(self, uniqname, location):
        curr_time = int(round(time.time()))

        if location == 'None':
            self.log.error(curr_datetime() + "ERROR - determining presence on None\n" + 
                    str(self.presences[uniqname]))
            return False

        # the person will definitely already have this location in their data dict
        person = self.presences[uniqname]
        evidence = person['location_data'][location]
        curr_location = person['location']
        last_seen_time = person['location_data'][location]['last_seen']

        # check if ble RSSI is strong enough
        if 'bleAddr' in evidence:
            for scanner in evidence['bleAddr']:
                # remove old data
                while (len(evidence['bleAddr'][scanner]['times']) > 0 and
                        curr_time-min(evidence['bleAddr'][scanner]['times']) > self.BLE_DURATION):
                    evidence['bleAddr'][scanner]['times'].pop(0)
                    evidence['bleAddr'][scanner]['rssis'].pop(0)

                # check if enough data is present and average is high enough
                if len(evidence['bleAddr'][scanner]['times']) > self.BLE_MINIMUM_COUNT:
                    avg_rssi = sum(evidence['bleAddr'][scanner]['rssis'])/len(evidence['bleAddr'][scanner]['rssis'])
                    evidence['bleAddr'][scanner]['avg_rssi'] = avg_rssi
                    if avg_rssi >= self.BLE_MIN_RSSI:
                        # BLE data is valid. We could be present
                        person['last_seen'] = max(evidence['bleAddr'][scanner]['times'])
                        person['location_data'][location]['last_seen'] = person['last_seen']
                        evidence['present_by'] = 'bleAddr'
                        evidence['potentially_present'] = True
                        return True
                else:
                    evidence['bleAddr'][scanner]['avg_rssi'] = -200

        #TODO: check if mac RSSI is strong enough
        #if 'macAddr' in evidence:

        #TODO: check on door data
        #if 'door' in evidence:

        # check if we have been seen recently
        if ((curr_time - last_seen_time) < self.HYSTERESIS):
            evidence['present_by'] = 'time'
            evidence['potentially_present'] = True
            return True

        evidence['present_by'] = 'None'
        evidence['potentially_present'] = False
        return False


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
                self.log.error(curr_datetime() + "ERROR - RabbitMQReceiver: " + str(e) + ' ' + repr(e))

    def _on_data(self, channel, method, prop, body):
        # data received from rabbitmq. Push to msg_queue
        self.message_queue.put([self.data_type, json.loads(body)])


class SocketIOReceiverThread (Thread):
    SOCKETIO_HOST = 'gatd.eecs.umich.edu'
    SOCKETIO_PORT = 8082
    SOCKETIO_NAMESPACE = 'stream'

    def __init__(self, profile_id, query, data_type, message_queue):

        # init thread
        super(SocketIOReceiverThread, self).__init__()
        self.daemon = True

        # init data
        self.profile_id = profile_id
        self.data_type = data_type
        self.message_queue = message_queue
        self.stream_namespace = None

        # make query. Note that this overrides the profile id with the user's
        #   choice if specified in query
        profile_query = {'profile_id': profile_id}
        self.query = dict(list(profile_query.items()) + list(query.items()))

        # start thread
        self.start()

    def run(self):
        while True:
            try:
                socketIO = sioc.SocketIO(self.SOCKETIO_HOST, self.SOCKETIO_PORT)
                self.stream_namespace = socketIO.define(StreamReceiver,
                        '/{}'.format(self.SOCKETIO_NAMESPACE))
                self.stream_namespace.set_data(self.query, self.data_type,
                        self.message_queue, self.stream_namespace)
                socketIO.wait()
            except sioc.exceptions.ConnectionError:
                # ignore error and continue
                socketIO.disconnect()


class StreamReceiver (sioc.BaseNamespace):

    def set_data (self, query, data_type, message_queue, stream_namespace):
        self.query = query
        self.data_type = data_type
        self.message_queue = message_queue
        self.stream_namespace = stream_namespace

    def on_reconnect (self):
        if 'time' in query:
            del query['time']
        self.stream_namespace.emit('query', self.query)

    def on_connect (self):
        self.stream_namespace.emit('query', self.query)

    def on_data (self, *args):
        # data received from gatd. Push to msg_q
        self.message_queue.put([self.data_type, args[0]])


class GATDPoster(Thread):
    def __init__(self, address, queue, log=None):
        # init thread
        super(GATDPoster, self).__init__()
        self.daemon = True

        # init data
        self.post_address = address
        self.msg_queue = queue
        self.log = log

        # autostart thread
        self.start()

    def run(self):
        while True:
            # look for a packet
            data = self.msg_queue.get()

            # post to GATD
            #XXX: Change this to do UDP posts instead of HTTP posts for speed
            try:
                req = urllib2.Request(self.post_address)
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


class RabbitMQPoster(Thread):
    def __init__(self, route_key, queue, log=None):

        # init thread
        super(RabbitMQPoster, self).__init__()
        self.daemon = True

        # init data
        self.route_key = route_key
        self.msg_queue = queue
        self.log = log

        # autostart thread
        self.start()

    def run(self):
        try:
            import config
        except ImportError:
            print('Cannot find config file. Need symlink from shed')
            sys.exit(1)

        while True:
            try:
                # Get a blocking connection to the rabbitmq
                self.amqp_conn = pika.BlockingConnection(
                        pika.ConnectionParameters(
                            host=config.rabbitmq['host'],
                            virtual_host=config.rabbitmq['vhost'],
                            credentials=pika.PlainCredentials(
                                config.rabbitmq['login'],
                                config.rabbitmq['password']))
                    )
                self.amqp_chan = self.amqp_conn.channel()

                while True:
                    # look for a packet
                    (data, route) = self.msg_queue.get()

                    # post to RabbitMQ
                    #print("\tPosting to route: " + self.route_key+'.'+route.replace(' ', '_').replace('|', '.') + '\n\t' + str(data))
                    self.amqp_chan.basic_publish(exchange=config.rabbitmq['exchange'],
                                        body=json.dumps(data),
                                        routing_key=self.route_key+'.'+route.replace(' ', '_').replace('|', '.'))

                    self.msg_queue.task_done()
            except Exception as e:
                self.log.error(curr_datetime() + "ERROR - RabbitMQPoster: " + str(e) + ' ' + repr(e))


if __name__=="__main__":
    main()

