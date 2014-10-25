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

BLEADDR_EXPLORE_ADDR = 'http://inductor.eecs.umich.edu:8085/explore/profile/' + BLEADDR_PROFILE_ID
WEARABOUTS_POST_ADDR = 'http://inductor.eecs.umich.edu:8081/' + WEARABOUTS_PROFILE_ID

def main( ):

    # setup logging
    log = logging.getLogger('whereabouts_log')
    log.setLevel(logging.DEBUG)
    log_filename = '../logs/weareabouts_log.out'
    handler = logging.handlers.TimedRotatingFileHandler(log_filename,
            when='midnight', backupCount=7)
    log.addHandler(handler)
    log.info("Running whereabouts controller...")
    print("Running whereabouts controller...")

    # start threads to receive data from GATD
    message_queue = Queue.Queue()
    ReceiverThread(BLEADDR_PROFILE_ID, {}, 'bleAddr', message_queue)
    #TODO: Reactivate these once they are written
    #ReceiverThread(DOOR_PROFILE_ID,    {}, 'door',    message_queue)
    #ReceiverThread(MACADDR_PROFILE_ID, {}, 'macAddr', message_queue)

    # start presence controller
    controller = PresenceController(message_queue, WEARABOUTS_POST_ADDR, log)
    #XXX: bring this back once it works
    #while True:
    #    try:
    #        controller.monitor()
    #    except Exception as e:
    #        log.error(curr_datetime() + "ERROR - PresenceController: " + str(e))
    controller.monitor()

def post_to_gatd(data, address, log=None):
    try:
        req = urllib2.Request(address)
        req.add_header('Content-Type', 'application/json')
        response = urllib2.urlopen(req, json.dumps(data))
    except (httplib.BadStatusLine, ullib2.URLError), e:
        # ignore error and carry on
        if log:
            log.error(curr_datetime() + "ERROR - Post to GATD: " + str(e))
        else:
            print(curr_datetime() + "ERROR - Post to GATD: " + str(e))

def curr_datetime():
    return time.strftime("%m/%d/%Y %H:%M:%S ")


class PresenceController ():
    #XXX: all of these parameters need tuning
    # how often locate should be run on everyone, seconds
    LOCATE_PERIOD = 10

    # how long to keep assuming someone is in the same room, seconds
    HYSTERESIS = 60

    # how long before a BLE sample is invalid, seconds
    BLE_DURATION = 30

    # minimum BLE RSSI that counts as in the room, dBm
    BLE_MIN_RSSI = -83

    # difference in BLE causing a room switch
    BLE_SWITCH_POINT = 10

    def __init__(self, queue, post_address, log):
        self.msg_queue = queue
        self.log = log
        self.post_address = post_address

        self.presences = {}
        self.last_locate_time = 0
        self.last_update = 0
        self.last_packet = 0
        self.start_time = time.time()

    def monitor(self):
        while True:

            data_type = 'None'
            pkt = None
            try:
                # wait for data from GATD
                [data_type, pkt] = self.msg_queue.get(timeout=5)
            except Queue.Empty:
                # No data has been seen, timeout to update presences
                pass

            self.update_screen()

            # automatically re-run locate if it's been static too long
            if ((time.time() - self.last_locate_time) > self.LOCATE_PERIOD):
                self.locate_everyone()

            # check data for validity
            if (pkt == None or 'location_str' not in pkt or 'time' not in pkt or
                    'uniqname' not in pkt):
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
                        'present_since': 0,
                        'last_seen': 0,
                        'confidence': 0,
                        'location_data': {}}
            person = self.presences[uniqname]

            # create location if necessary
            location = pkt['location_str']
            if location not in person['location_data']:
                person['location_data'][location] = {
                        'potentially_present': False,
                        'present_by': 'None'}
            evidence = person['location_data'][location]

            # handle bleAddr data
            if data_type == 'bleAddr':
                # specific field validity testing
                if 'avg_rssi' not in pkt or 'rssi' not in pkt:
                    self.log.error(curr_datetime() + " Got an invalid ble packet")
                    continue

                # create dict if necessary
                if 'bleAddr' not in evidence:
                    evidence['bleAddr'] = {
                            'time': 0,
                            'rssi': -200,
                            'address': ''
                            }

                # update user information
                timestamp = int(round(pkt['time']/1000))
                if timestamp > evidence['bleAddr']['time']:
                    evidence['bleAddr']['time'] = timestamp
                    #XXX: think about fixing me maybe
                    #evidence['bleAddr']['rssi'] = pkt['avg_rssi']
                    evidence['bleAddr']['rssi'] = pkt['rssi']
                    evidence['bleAddr']['address'] = pkt['ble_addr']

                # locate the user based on this new information. Only relocate
                #   if the person may have entered or left, which is noted by
                #   a mismatch in determine_presence and in_location
                # Note: this isn't exactly perfect. It could fail if the user
                #   is really close to being in two locations (defaults to
                #   keeping the user in the same location). But, we are
                #   re-running locate_everyone() pretty often anyways, so this
                #   is really just here as a heuristic to speed up locating
                #XXX: This could be pulled out for the demo
                if (self.determine_presence(uniqname, location) !=
                        self.in_location(uniqname, location)):
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

    def update_screen(self):
        SCREEN_LINES = 52

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
                if index == 52:
                    break

    def _print_person(self, index, uniqname):
        person = self.presences[uniqname]
        location = person['location']

        rssi = -200
        if location != 'None':
            rssi = person['location_data'][location]['bleAddr']['rssi']

        print_str = "(" + str(index) + ")" + \
                "\tName: " + str(person['full_name']) + \
                ('\t' if len(person['full_name']) > 9 else '\t\t') + \
                "Loc: " + str(location.split('|')[-1]) + \
                "\tRSSI: " + str(rssi) + \
                "\tAgo: " + str(int(round(time.time() - person['last_seen'])))

        print(print_str)

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
        for uniqname in self.presences:
            self.locate_person(uniqname)

    # some function to go through each location in a person and figure out where they are
    #   also posts to GATD if there is a change
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
                return 'None'

            # try choosing the best based on BLE
            ble_locs = [location for location in possible_locations
                    if (self.present_by('bleAddr', uniqname, location))]
            if (len(ble_locs) != 0):

                # get best rssi and locations with that rssi
                rssi_loc_pairs = [(loc, person['location_data'][loc]['bleAddr']['rssi']) 
                        for loc in possible_locations]
                best_rssi = max(rssi_loc_pairs, key = lambda x: x[1])[1]
                best_rssi_locs = [item[0] for item in rssi_loc_pairs
                        if item[1] == best_rssi]

                new_location = 'None'
                confidence = 0
                if curr_location in best_rssi_locs:
                    # current location still the best
                    new_location = curr_location
                    confidence = (1 - (-best_rssi)/101.0)
                elif not self.present_by('bleAddr', uniqname, curr_location):
                    # new location has ble which is best
                    new_location = random.choice(best_rssi_locs)
                    confidence = (1 - (-best_rssi)/101.0)
                else:
                    # only pick new location if ble is sufficiently higher
                    curr_rssi = person['location_data'][curr_location]['bleAddr']['rssi']
                    if ((best_rssi - curr_rssi) > self.BLE_SWITCH_POINT):
                        new_location = random.choice(best_rssi_locs)
                        confidence = (1 - (-best_rssi)/101.0)
                    else:
                        new_location = curr_location
                        confidence = (1 - (-curr_rssi)/101.0)

                self.set_location(uniqname, new_location, confidence)
                return new_location

            #TODO: try choosing the best based on MAC

            #TODO: try choosing the best based on Door

            # choose the best based on time. This means staying at the current location
            new_location = curr_location
            self.set_location(uniqname, new_location, 0.2)
            return new_location

    def set_location(self, uniqname, location, confidence):
        curr_time = time.time()
        person = self.presences[uniqname]
        curr_location = person['location']

        person['confidence'] = max(confidence, 0)

        post_data = False
        if (location != curr_location):
            person['location'] = location
            person['present_since'] = curr_time
            post_data = True

        present_by = 'None'
        if location != 'None':
            present_by = person['location_data'][location]['present_by']

        #XXX: if there is too much data, this could be limited to location
        #   changes only, rather than on any update
        # post to GATD
        if post_data:
            data = {'uniqname': uniqname,
                    'full_name': person['full_name'],
                    'location_str': person['location'],
                    'present_since': person['present_since'],
                    'last_seen': person['last_seen'],
                    'confidence': person['confidence'],
                    'present_by': present_by}
            post_to_gatd(data, self.post_address, self.log)

        self.log_status(uniqname, location, present_by)

    # some function to go through a single location in a person and figure out if they could be in it
    def determine_presence(self, uniqname, location):
        curr_time = int(round(time.time()))

        if location == 'None':
            self.log.error(curr_datetime() + "ERROR - determining presence on None\n" + 
                    str(self.presences[uniqname]))
            return False

        person = self.presences[uniqname]
        evidence = person['location_data'][location]
        curr_location = person['location']
        last_seen_time = person['last_seen']

        # check if ble RSSI is strong enough
        if 'bleAddr' in evidence:
            if ((curr_time - evidence['bleAddr']['time']) < self.BLE_DURATION and
                    evidence['bleAddr']['rssi'] >= self.BLE_MIN_RSSI):
                person['last_seen'] = evidence['bleAddr']['time']
                evidence['present_by'] = 'bleAddr'
                evidence['potentially_present'] = True
                return True

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


class ReceiverThread (Thread):
    SOCKETIO_HOST = 'inductor.eecs.umich.edu'
    SOCKETIO_PORT = 8082
    SOCKETIO_NAMESPACE = 'stream'

    def __init__(self, profile_id, query, data_type, message_queue):

        # init thread
        super(ReceiverThread, self).__init__()
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


if __name__=="__main__":
    main()

