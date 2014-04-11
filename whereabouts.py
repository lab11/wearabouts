#!/usr/bin/env python2

# TODO: periodic polling, even if low frequency, would be super convenient.

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
logging.basicConfig()

USAGE = """
Pulls data from various GATD streams to determine people in a given room

To perform continuous monitoring, please specify location being monitored.

Locations should be specified in the format:
    "University|Building|Room"

Fitbits are monitored in the following locations:"""

FITBIT_GET_ADDR = 'http://memristor-v1.eecs.umich.edu:8085/explore/profile/dwgY2s6mEu'

SOCKETIO_HOST      = 'inductor.eecs.umich.edu'
SOCKETIO_PORT      = 8082
SOCKETIO_NAMESPACE = 'stream'

def main( ):

    # get location from user
    location = ''
    if len(sys.argv) != 2:
        print(USAGE)
        fitbit_locs = get_fitbit_locations()
        for loc in fitbit_locs:
            print("    \"" + loc + "\"")
        print("")
        exit()
    else:
        location = sys.argv[1]

    fitbit_query = {'profile_id': 'dwgY2s6mEu', 'location_str': location}
    door_query = {'profile_id': 'U8H29zqH0i', 'location_str': location}
    message_queue = Queue.Queue()

    # start threads to receive data from GATD
    ReceiverThread(fitbit_query, 'fitbit', message_queue)
    ReceiverThread(door_query, 'door', message_queue)

    # start migration monitor
    mm = MigrationMonitor(location, message_queue)
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


class MigrationMonitor ( ):
    people_present = {} # mapping of people present to evidence of presence

    fitbit_group = []

    def __init__(self, location, message_queue):
        self.location = location
        self.message_queue = message_queue

    def monitor(self):
        while True:
            try:
                [data_type, pkt] = self.message_queue.get(timeout=3)
            except Queue.Empty:

                # fitbit data comes in discovery scan groupings. If too much
                #   time has passed between packets, we can assume that the
                #   group is completed
                if self.fitbit_group:
                    for person in self.fitbit_group:
                        # None is a special ID signifying no fitbits were found
                        if person != 'None':
                            if person not in self.people_present:
                                print(cur_datetime() + ": " + person + " has appeared in " + str(self.location) + "\n")
                                self.people_present[person] = 'fitbit'
                            else:
                                self.people_present[person] = 'fitbit'

                    del_list = []
                    for person in self.people_present:
                        if person not in self.fitbit_group:
                            if (self.people_present[person] == 'fitbit'):
                                print(cur_datetime() + ": " + person + " has left " + str(self.location) + "\n")
                            else:
                                print(cur_datetime() + ": Can't be sure " + person + " is still in " + str(self.location) + "\n")
                                
                            del_list.append(person)

                    for person in del_list:
                        del self.people_present[person]

                    self.fitbit_group = []
                    #print ("Emptied fitbit group")

                # There's no data available yet
                continue

            # skip packet if not fully formed
            if 'full_name' not in pkt:
                continue
            if 'location_str' not in pkt:
                continue
            if 'time' not in pkt:
                continue

            # skip packet if not for this location
            if pkt['location_str'] != self.location:
                continue

            #print("Got a packet!")

            # the way this works:
            #   people_present is a mapping of people in the location to
            #   evidence of them being there. Each individual sensor adds
            #   a person if not in the list already and can either overwrite
            #   evidence or choose not to based on its priority level. Sensors
            #   should also remove people from the list when they are no
            #   longer present based on any data other than its own (or if its
            #   data is of a higher priority)

            # fitbit data
            # This data comes in discovery scan groups. Fill a list with the
            #   group members and only add their information to people_present
            #   on a timeout. If a person is no longer found, assume they are
            #   not present
            if data_type == 'fitbit':
                person = pkt['full_name']
                if person not in self.fitbit_group:
                    self.fitbit_group.append(person)
                #print ("Fitbit Packet!")
                
            # door sensor data
            # This data comes in three forms: door_open, door_close, and rfid.
            #   The rfid is used to identify that an individual is present and
            #   is valid until another door event or fitbit group occurs
            if data_type == 'door':
                if 'type' in pkt and pkt['type'] == 'rfid':
                    person = pkt['full_name']
                    print("\n" + cur_datetime() + ": " + person + " has entered " + str(self.location) + "\n")
                    self.people_present[person] = 'rfid'
                #print("Door packet!")

            # Add additional sources here
            # if data_type == 'New Thing':


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
        socketIO = sioc.SocketIO(SOCKETIO_HOST, SOCKETIO_PORT)
        self.stream_namespace = socketIO.define(StreamReceiver, '/{}'.format(SOCKETIO_NAMESPACE))
        self.stream_namespace.set_data(self.query, self.data_type, self.message_queue, self.stream_namespace)
        socketIO.wait()


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

