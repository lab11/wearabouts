#!/usr/bin/env python2

# TODO: periodic polling, even if low frequency, would be super convenient.

import IPy
import json
import sys
from threading import Thread
import Queue
from time import time

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

example:
    "University of Michigan|BBB|4908"
"""

SOCKETIO_HOST      = 'inductor.eecs.umich.edu'
SOCKETIO_PORT      = 8082
SOCKETIO_NAMESPACE = 'stream'

def main( ):

    # get location from user
    location = ''
    if len(sys.argv) != 2:
        print(USAGE)
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


class MigrationMonitor ( ):
    people_present = {} # mapping of people present to evidence of presence
    last_seen_rfids = {}
    previous_message_time = 0

    def __init__(self, location, message_queue):
        self.location = location
        self.message_queue = message_queue

    def monitor(self):
        while True:
            [data_type, packet] = self.message_queue.get(false)

            if packet = None:
                
                # Do something if enough time has passed
                if time() - previous_message_time > 30:
                    #XXX: do stuff

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

            # the way this works:
            #   people_present is a mapping of people in the location to
            #   evidence of them being there. Each individual sensor adds
            #   a person if not in the list already and can either overwrite
            #   evidence or choose not to based on its priority level. Sensors
            #   should also remove people from the list when they are no
            #   longer present based on any data other than its own (or if its
            #   data is of a higher priority)

            # fitbit data
            if data_type == 'fitbit':
                person = pkt['full_name']
                #XXX: do stuff
                    
                
            # door sensor data
            if data_type == 'door':
                if 'type' in pkt and pkt['type'] == 'rfid':
                    person = pkt['full_name']
                    self.last_seen_rfids[person] = 1
                    print("\n" + cur_datetime() + ": " + person + " has entered " + str(location) + "\n")
                    people_present[person] = 'rfid'
                if 'type' in pkt and pkt['type'] == 'door_open':
                    # keep rfid people around until the door opens again
                    for person in last_seen_rfids.keys():
                        if self.last_seen_rfids[person] == 1:
                            self.last_seen_rfids[person] = 0
                        if self.last_seen_rfids[person] == 0:
                            del self.last_seen_rfids[person]
                            # only remove the person if they don't have other evidence
                            if person in self.people_present and self.people_present[person] == 'rfid':
                                print("\n" + cur_datetime() + ": Can't be sure " + person + " is still in " + str(location) + "\n")
                                del self.people_present[person]


            # Add additional sources here
            # if data_type == 'New Thing':

            # mark the time this packet was seen at
            self.previous_message_time = time()


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




if 0:

    import fitbitfinder
    from time import sleep
    from time import strftime

    try:
        import socketIO_client as sioc
    except ImportError:
        print('Could not import the socket.io client library.')
        print('sudo pip install socketIO-client')
        sys.exit(1)

    import logging
    logging.basicConfig()

    DEVICE_MAP_FILE = "device-map.json"
    LOCATION = ""
    query = {'profile_id': 'U8H29zqH0i',
             'address': None} #specified in main once location is known
    stream_namespace = None

    # gets deployment location, picks door-triggered or polling monitor
    # depending on whether there is a door sensor available.
    # it would be nice to generalize this trigger idea in the future.
    def main():
        global LOCATION
        global stream_namespace
        SOCKETIO_HOST      = 'inductor.eecs.umich.edu'
        SOCKETIO_PORT      = 8082
        SOCKETIO_NAMESPACE = 'stream'

        LOCATION = "" #Get this as a system argument
        DOOR_TRIGGERED = False #Get this as a system argument

        USAGE = """
        Please specify location being monitored.

        if no door sensor is present at the specified location,
        the program defaults to polling periodically.

        Door sensors are available in the following locations:
    """
        door_sensors = get_door_sensors()

        # get location
        if len(sys.argv) != 2:
            print(USAGE)
            for sensor in door_sensors:
                print("    " + sensor['location'])
            print("")
            exit()
        else:
            LOCATION = sys.argv[1]

        # if location has door sensor, trigger on it
        for sensor in door_sensors:
            if sensor['location'] == LOCATION:
                DOOR_TRIGGERED = True
                query['address'] = sensor['device_addr']

        # door/gatd triggered logic
        if DOOR_TRIGGERED:
            print("Starting door-triggered migration monitor")
            socketIO = sioc.SocketIO(SOCKETIO_HOST, SOCKETIO_PORT)
            stream_namespace = socketIO.define(EventDrivenMigrationMonitor,
                '/{}'.format(SOCKETIO_NAMESPACE))
            socketIO.wait()
        # periodic polling only
        else:
            print("Starting polling migration monitor")
            PollingMigrationMonitor(30*60) # poll every 30 mins + time to find devices
            #PollingMigrationMonitor(1)
        while(True):
            pass

    def get_door_sensors():
        door_sensors = []
        f = open(DEVICE_MAP_FILE)
        contents = f.read()
        f.close()
        contents = contents.replace("\n", "")
        contents = contents.replace("\t", "")
        device_maps = json.loads(contents)
        for device_map in device_maps:
            if device_map["descr"] == "door sensor":
                door_sensors.append(device_map)
        return door_sensors

    def sanitize(device_id):
        return device_id.replace(":", "").upper()

    def cur_datetime():
        return strftime("%m/%d/%Y %H:%M")

    def get_real_name(uniqname):
        real_name = "Unknown Name"
        f = open(DEVICE_MAP_FILE)
        contents = f.read()
        f.close()
        contents = contents.replace("\n", "")
        contents = contents.replace("\t", "")
        device_maps = json.loads(contents)
        for device_map in device_maps:
            if "uniqname" in device_map and device_map["uniqname"] == uniqname:
                real_name = device_map["owner"]
        return real_name

    class MigrationMonitor():
        last_seen_owners = None
        last_seen_rfids = {} #keep these around for a scan

        def update(self):
            # check for present fitbits.
            present_fitbits = self.get_present_fitbits()
            # match fitbit list against known list
            migrants = self.get_migrants(present_fitbits)
            # send these changes to GATD

        def get_present_fitbits(self):
            present_fitbits = []
            for i in range(3):
                fitbit_data = fitbitfinder.discover_fitbits()
                # if timeout, try again
                if fitbit_data == None:
                    i = i-1
            if fitbit_data != None:
                # sanitize
                for i,fitbit_record in enumerate(fitbit_data):
                    fitbit_id = sanitize(fitbit_record[0])
                    if fitbit_id not in present_fitbits:
                        present_fitbits.append(fitbit_id)
            return present_fitbits

        def get_migrants(self, present_fitbits):
            present_owners = self.get_device_owners(present_fitbits)
            print("Current occupants:")
            if present_owners == []:
                print("None.")
            else:
                for p in present_owners:
                    print(" " + str(p))
                    delete_list = []
                    # this takes care of people who card in and then whose fitbit shows up
                    if p in self.last_seen_rfids and p not in self.last_seen_owners:
                        self.last_seen_owners.append(p)
                        delete_list.append(p)
                    for p in delete_list:
                        del self.last_seen_rfids[p]
            if self.last_seen_owners != None:
                appeared = [p for p in present_owners if p not in self.last_seen_owners]
                disappeared = [p for p in self.last_seen_owners if p not in present_owners]
                delete_list = []
                for p in self.last_seen_rfids:
                    if self.last_seen_rfids[p] == 0:
                        delete_list.append(p)
                    else:
                        self.last_seen_rfids[p] -= 1
                for p in delete_list:
                    del self.last_seen_rfids[p]
                #debug
                for p in appeared:
                    print("\n" + cur_datetime() + ": " + str(p) + " has entered " + str(LOCATION) + "\n")
                #debug
                for p in disappeared:
                    print("\n" + cur_datetime() + ": " + str(p) + " has left " + str(LOCATION) + "\n")
            self.last_seen_owners = present_owners

        def get_device_owners(self, devices):
            owners = []
            f = open(DEVICE_MAP_FILE)
            contents = f.read()
            f.close()
            contents = contents.replace("\n", "")
            contents = contents.replace("\t", "")
            device_maps = json.loads(contents)
            for device_map in device_maps:
                if sanitize(device_map["device_addr"]) in devices and device_map["owner"] not in owners:
                    owners.append(device_map["owner"])
            return owners


    # looks for migration sets after a door event occurs
    class EventDrivenMigrationMonitor (sioc.BaseNamespace, MigrationMonitor):

        def on_reconnect (self):
            if 'time' in query:
                del query['time']
            stream_namespace.emit('query', query)

        def on_connect (self):
            stream_namespace.emit('query', query)

        def on_data (self, *args):
            pkt = args[0]
            msg_type = pkt['type']
            print(cur_datetime() + ": " + pkt['type'].replace('_', ' ').capitalize() + " (" + str(LOCATION) + ")")
            # people leaving
            if msg_type == 'door_close':
                self.update() # enough latency due to multiple checks that they have enough time to escape
            # people entering. Covers folks who didn't swipe their RFID card (multiple people, keys, etc.)
            elif msg_type == 'door_open':
                self.update()
            # people entering. Covers the person who carded in (way faster than finding fitbit)
            elif pkt['type'] == 'rfid':
                person = get_real_name(pkt['uniqname'])
                if self.last_seen_owners != None and person not in self.last_seen_owners:
                    self.last_seen_rfids[person] = 1 #number of scans to remember their entry
                    print("\n" + cur_datetime() + ": " + person + " has entered " + str(LOCATION) + "\n")
                    #send to GATD
                self.update()


    # looks for migration events periodically
    # i.e., does not require a door sensor
    class PollingMigrationMonitor(Thread, MigrationMonitor):

        def __init__(self, interval_secs):
            # thread stuff
            super(PollingMigrationMonitor, self).__init__()
            self.daemon = True
            self.cancelled = False
            # logic parameters
            self.interval_secs = interval_secs
            # gooooooooo
            self.start()

        def run(self):
            while not self.cancelled:
                print("\nPolling {}".format(strftime("%Y-%m-%d %H:%M:%S")))
                self.update()
                sleep(self.interval_secs)

        def cancel(self):
            self.cancelled = True

    if __name__=="__main__":
        main()

