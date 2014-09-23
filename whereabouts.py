#!/usr/bin/env python2

import IPy
import json
import sys
from threading import Thread
import Queue
import time
import urllib2

try:
    import socketIO_client as sioc
except ImportError:
    print('Could not import the socket.io client library.')
    print('sudo pip install socketIO-client')
    sys.exit(1)

import logging
import logging.handlers

USAGE = """
Pulls data from various GATD streams to determine people in a given room

To perform continuous monitoring, please specify location being monitored.

Locations should be specified in the format:
    University|Building|Room

Fitbits are monitored in the following locations:"""

FITBIT_GET_ADDR = 'http://inductor.eecs.umich.edu:8085/explore/profile/dwgY2s6mEu'
PRESENCE_POST_ADDR = 'http://inductor.eecs.umich.edu:8081/hsYQx8blbd'

SOCKETIO_HOST      = 'inductor.eecs.umich.edu'
SOCKETIO_PORT      = 8082
SOCKETIO_NAMESPACE = 'stream'

def main( ):
    # get location from user
    location = ''
    if len(sys.argv) != 2:
        print(USAGE)
        fitbit_locs = get_fitbit_locations()
        index = 0
        for sensor_loc in fitbit_locs:
            print("    [" + str(index) + "]: " + sensor_loc)
            index += 1
        print("")
        user_input = raw_input("Select a location or enter a new one: ")

        if user_input == '':
            print("Invalid selection")
            exit()

        if user_input.isdigit():
            user_input = int(user_input)
            if 0 <= user_input < index:
                location = fitbit_locs[user_input]
            else:
                print("Invalid selection")
                exit()
        else:
            location = user_input
    else:
        location = sys.argv[1]

    print("Running whereabouts at " + location)

    # setup logging
    log = logging.getLogger('whereabouts_log')
    log.setLevel(logging.DEBUG)
    log_filename = 'whereabouts_log_' + str(location.split('|')[-1]) + '.out'
    handler = logging.handlers.TimedRotatingFileHandler(log_filename,
            when='midnight', backupCount=7)
    log.addHandler(handler)
    log.info("Running whereabouts at " + location)

    # gatd data
    fitbit_query = {'profile_id': 'dwgY2s6mEu', 'location_str': location}
    door_query = {'profile_id': 'U8H29zqH0i', 'location_str': location}
    macAddr_query = {'profile_id': 'PGMR22B9wP', 'location_str': location}
    message_queue = Queue.Queue()

    # start threads to receive data from GATD
    ReceiverThread(fitbit_query, 'fitbit', message_queue)
    ReceiverThread(door_query, 'door', message_queue)
    ReceiverThread(macAddr_query, 'macAddr', message_queue)

    # start migration monitor
    mm = MigrationMonitor(location, message_queue, log)
    mm.monitor()

def cur_datetime():
    return time.strftime("%m/%d/%Y %H:%M")

def get_fitbit_locations():

    # query GATD explorer to find fitbit sensor locations
    req = urllib2.Request(FITBIT_GET_ADDR)
    response = urllib2.urlopen(req)
    json_data = json.loads(response.read())

    if 'location_str' in json_data:
        return json_data['location_str'].keys()
    else:
        return ['None']

def post_to_gatd(location, people_list, present_since, log=None):

    # Create standard data
    data = {
            'location_str' : location,
            'person_list' : sorted(people_list),
            'since_list' : sorted(present_since)
            }

    # print the current list of people
    print(cur_datetime() + ": " + str([person.keys()[0] for person in people_list]))
    if log:
        log.info(cur_datetime() + ": " + str([person.keys()[0] for person in people_list]) + "\n")

    #print("starting post to GATD of" + str(json.dumps(data)))
    req = urllib2.Request(PRESENCE_POST_ADDR)
    req.add_header('Content-Type', 'application/json')

    # Actually post to GATD
    response = urllib2.urlopen(req, json.dumps(data))
    #print("POST complete")


class MigrationMonitor ( ):
    presence_data = {}
    fitbit_group = {}

    def __init__(self, location, message_queue, log):
        self.location = location
        self.message_queue = message_queue
        self.log = log

        self.last_locate = 0
        self.last_fitbit = 0

    def monitor(self):
        while True:
            data_type = 'None'
            pkt = None
            try:
                # Pull data from message queue
                [data_type, pkt] = self.message_queue.get(timeout=10)

            except Queue.Empty:
                # No data has been seen, handle timeouts
                pass

            current_time = int(round(time.time()))

            # fitbit data comes in discovery scan groupings. If too much
            #   time has passed between packets, we can assume that the
            #   group is completed
            if ((current_time - self.last_fitbit) > 12 and self.fitbit_group):
                for uniqname in self.presence_data:
                    # create dict for user
                    if 'fitbit' not in self.presence_data[uniqname]:
                        self.presence_data[uniqname]['fitbit'] = {}

                    # add data for user
                    if uniqname in self.fitbit_group:
                        self.presence_data[uniqname]['fitbit']['rssi'] = self.fitbit_group[uniqname]
                    else:
                        #print(cur_datetime() + "Changing " + uniqname + " to -100")
                        self.presence_data[uniqname]['fitbit']['rssi'] = -100
                    self.presence_data[uniqname]['fitbit']['time'] = current_time

                self.fitbit_group = {}
                self.locate()

            # automatically re-run locate if it's been static for 5 minutes
            if (current_time - self.last_locate) > 5*60:
                self.locate()

            # skip packet if it doesn't contain enough data for whereabouts use
            if pkt == None:
                continue
            if 'location_str' not in pkt:
                continue
            if 'time' not in pkt:
                continue

            # skip packet if not for this location
            if pkt['location_str'] != self.location:
                continue

            # get uniqname from packet
            uniqname = ''
            if 'uniqname' in pkt:
                if 'full_name' not in pkt:
                    continue
                uniqname = pkt['uniqname']
                if uniqname not in self.presence_data and uniqname != 'None':
                    self.presence_data[uniqname] = {}
                    self.presence_data[uniqname]['full_name'] = pkt['full_name']
                    self.presence_data[uniqname]['present_since'] = 0
            # allow packets to continue without uniqname in order to handle door events

            # MAC address data
            # This data comes in single packets identifying a detected MAC
            #   address, timestamp, and RSSI value (averaged over one minute).
            # People present records rssi of the most recent scan as well as
            #   the time. Too low of an RSSI means not in the room. Too long
            #   since a packet has been received means not in the room.
            if data_type == 'macAddr' and uniqname != '':
                if 'avg_rssi' not in pkt or 'time' not in pkt:
                    continue

                self.log.debug(cur_datetime() + ' MAC: ' + str(pkt))

                # create dict for user
                if 'macAddr' not in self.presence_data[uniqname]:
                    self.presence_data[uniqname]['macAddr'] = {}

                # check that this timestamp is as new as the most recent packet
                timestamp = int(round(pkt['time']/1000))
                if 'time' in self.presence_data[uniqname]['macAddr'] and
                        not timestamp >= self.presence_data[uniqname]['macAddr']['time']:
                    self.log.error(cur_datetime() + " : out of sequence packet.\n"+str(pkt))
                    continue

                # update user information
                self.presence_data[uniqname]['macAddr']['rssi'] = pkt['avg_rssi']
                self.presence_data[uniqname]['macAddr']['time'] = int(round(pkt['time']/1000))
                self.presence_data[uniqname]['macAddr']['mac_addr'] = pkt['mac_addr']
                self.locate()

            # fitbit data
            # This data comes in discovery scan groups. Keep a list of group
            #   members and only pass off to locate on a timeout
            # People present records rssi of the most recent scan, -100 means
            #   the person was not seen
            if data_type == 'fitbit':
                self.last_fitbit = current_time

                # add user to grouping of fitbit data
                if uniqname != 'None':
                    #print("Got fitbit data")
                    self.fitbit_group[uniqname] = pkt['rssi']
                else:
                    #print("Rewriting " + uniqname + " to -100")
                    self.fitbit_group[uniqname] = -100

            # door sensor data
            # This data comes in three forms: door_open, door_close, and rfid.
            #   The rfid is used to identify that an individual is present.
            #   Future door open events lead to a possibility that the
            #   individual has left
            # People present records timestamp of last rfid event and number of
            #   door open events since last rfid scan
            if data_type == 'door':
                if 'type' not in pkt or 'time' not in pkt:
                    continue

                if pkt['type'] == 'rfid':
                    # create dict for user
                    if 'door' not in self.presence_data[uniqname]:
                        self.presence_data[uniqname]['door'] = {}
                    # update user information
                    self.presence_data[uniqname]['door']['time'] = int(round(pkt['time']/1000))
                    self.presence_data[uniqname]['door']['open_count'] = 0
                    self.locate()

                if pkt['type'] == 'door_open':
                    for present_uniqname in self.presence_data:
                        if ('door' in self.presence_data[present_uniqname]):
                            self.presence_data[present_uniqname]['door']['open_count'] += 1
                    self.locate()

    def locate(self):
        self.last_locate = int(round(time.time()))

        # create list of people. Each person is a dict of {uniqname: full_name}
        people_present = []

        # create a list of when each person has been in lab since. Dict of {uniqname: start time}
        present_since = []

        # decide who is here
        for uniqname in self.presence_data:
            #print(uniqname + ": " + str(determine_presence(self.presence_data[uniqname])) + "\n"
            #        + str(self.presence_data[uniqname]))

            if self.determine_presence(self.presence_data[uniqname], uniqname):
                # person has been found to be present at this location
                if (self.presence_data[uniqname]['present_since'] == 0):
                    self.presence_data[uniqname]['present_since'] = self.last_locate

                # add to lists
                people_present.append({uniqname: self.presence_data[uniqname]['full_name']})
                present_since.append({uniqname: self.presence_data[uniqname]['present_since']})

            else:
                # person is not present
                self.presence_data[uniqname]['present_since'] = 0

        #post to GATD
        post_to_gatd(self.location, people_present, present_since, log=self.log)

    def determine_presence(self, data, uniqname):
        current_time = int(round(time.time()))

        if 'fitbit' in data:
            # if the rssi of the fitbit data supports user as in the room
            if ((current_time - data['fitbit']['time']) < 10*60 and
                    data['fitbit']['rssi'] >= -83):
                self.log.debug(uniqname + " present by fitbit " + str(data))
                self.presence_data[uniqname]['last_seen'] = current_time
                return True

        if 'macAddr' in data:
            #XXX: -50 is an arbitrary choice. Need to actually look at distributions
            #   especially the conference room
            if ((current_time - data['macAddr']['time']) < 5*60 and 
                    data['macAddr']['rssi'] >= -50):
                # if they were seen less than 5 minutes ago and the rssi supports
                #   the user as in the room
                self.log.debug(uniqname + " present by macAddr " + str(data))
                self.presence_data[uniqname]['last_seen'] = current_time
                return True

        if 'door' in data:
            # if the door hasn't been opened since they swiped and its been
            #   less than half an hour
            if ((current_time - data['door']['time'] < 30*60) and
                    data['door']['open_count'] < 2):
                self.log.debug(uniqname + " present by rfid " + str(data))
                self.presence_data[uniqname]['last_seen'] = current_time
                return True

        #XXX: This is good for stability but bad for immediate accuracy
        if 'last_seen' in data:
            # add a hysteresis so that people are counted as "in" for at least
            #   a full minute. But don't update the last_seen time!
            if ((current_time - data['last_seen']) < 60):
                self.log.debug(uniqname + " present by time " + str(data))
                return True

        self.log.debug(uniqname + " not present: " + str(data))
        return False


class ReceiverThread (Thread):

    def __init__(self, query, data_type, message_queue):

        # init thread
        super(ReceiverThread, self).__init__()
        self.daemon = True

        # init data
        self.query = query
        self.data_type = data_type
        self.message_queue = message_queue
        self.stream_namespace = None

        # start thread
        self.start()

    def run(self):
        while True:
            try:
                socketIO = sioc.SocketIO(SOCKETIO_HOST, SOCKETIO_PORT)
                self.stream_namespace = socketIO.define(StreamReceiver, '/{}'.format(SOCKETIO_NAMESPACE))
                self.stream_namespace.set_data(self.query, self.data_type, self.message_queue, self.stream_namespace)
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

