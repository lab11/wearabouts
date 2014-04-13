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
logging.basicConfig()

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

def post_to_gatd(location, people_present):

    # Create list of people
    people_list = []
    for uniqname in people_present.keys():
        people_list.append({uniqname: people_present[uniqname]})

    # Create standard data
    data = {
            'location_str' : location,
            'person_list' : sorted(people_list)
            }

    # print the current list of people
    print(cur_datetime() + ": " + str(people_present.keys()) + "\n")

    #print("starting post to GATD of" + str(json.dumps(data)))
    req = urllib2.Request(PRESENCE_POST_ADDR)
    req.add_header('Content-Type', 'application/json')

    # Actually post to GATD
    response = urllib2.urlopen(req, json.dumps(data))
    #print("POST complete")


class MigrationMonitor ( ):
    people_present = {}
    fitbit_group = {}

    def __init__(self, location, message_queue):
        self.location = location
        self.message_queue = message_queue

    #XXX: Need to think of a better way to do this
    def monitor(self):
        while True:
            try:
                [data_type, pkt] = self.message_queue.get(timeout=3)
            except Queue.Empty:

                # fitbit data comes in discovery scan groupings. If too much
                #   time has passed between packets, we can assume that the
                #   group is completed
                if self.fitbit_group:
                    for uniqname in self.fitbit_group.keys():
                        # None is a special ID signifying no fitbits were found
                        if uniqname != 'None':
                            self.people_present[uniqname] = self.fitbit_group[uniqname]

                    del_list = []
                    for uniqname in self.people_present.keys():
                        if uniqname not in self.fitbit_group.keys():
                            del_list.append(uniqname)

                    for uniqname in del_list:
                        del self.people_present[uniqname]

                    self.fitbit_group = {}

                    # Transmit updated people list to GATD
                    post_to_gatd(self.location, self.people_present)

                # There's no data available yet
                continue

            # skip packet if not fully formed
            if 'uniqname' not in pkt:
                continue
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
            #   uniqname. Each individual sensor adds a person if not in the
            #   list already. Sensors should also remove people from the list
            #   when they are no longer present

            # fitbit data
            # This data comes in discovery scan groups. Fill a list with the
            #   group members and only add their information to people_present
            #   on a timeout. If a person is no longer found, assume they are
            #   not present
            if data_type == 'fitbit':
                uniqname = pkt['uniqname']
                if uniqname not in self.fitbit_group:
                    self.fitbit_group[uniqname] = pkt['full_name'];
                #print ("Fitbit Packet!")
                
            # door sensor data
            # This data comes in three forms: door_open, door_close, and rfid.
            #   The rfid is used to identify that an individual is present and
            #   is valid until another door event or fitbit group occurs
            if data_type == 'door':
                if 'type' in pkt and pkt['type'] == 'rfid':
                    uniqname = pkt['uniqname']
                    #print("\n" + cur_datetime() + ": " + person + " has entered " + str(self.location) + "\n")
                    self.people_present[uniqname] = pkt['full_name']

                    # Transmit updated people list to GATD
                    post_to_gatd(self.location, self.people_present)

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

