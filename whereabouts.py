#!/usr/bin/env python

import IPy
import json
import sys
from threading import Thread
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
    # periodic polling logic
    else:
        print("Starting polling migration monitor")
        #PollingMigrationMonitor(30*60) # poll every 30 mins + time to find devices
        PollingMigrationMonitor(1)
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
        for p in present_owners:
            print(" " + str(p))
            # this takes care of people who card in and then whose fitbit shows up
            if p in self.last_seen_rfids and p not in self.last_seen_owners:
                self.last_seen_owners.append(p)
                del self.last_seen_rfids[p]
        if self.last_seen_owners != None:
            appeared = [p for p in present_owners if p not in self.last_seen_owners]
            disappeared = [p for p in self.last_seen_owners if p not in present_owners]
            for p in self.last_seen_rfids:
                if self.last_seen_rfids[p] == 0:
                    del self.last_seen_rfids[p]
                else:
                    self.last_seen_rfids[p] -= 1
            #debug
            for p in appeared:
                print("\n" + strftime("%m/%d/%Y %H:%M") + ": " + str(p) + " has entered " + str(LOCATION))
            #debug
            for p in disappeared:
                print("\n" + strftime("%m/%d/%Y %H:%M") + ": " + str(p) + " has left " + str(LOCATION)) 
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
        print("\n" + pkt['type'].replace('_', ' ').capitalize() + " (" + str(LOCATION) + ")")
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
                print(strftime("%m/%d/%Y %H:%M") + ": " + person + " has entered " + str(LOCATION) + "\n")
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
            self.update()
            sleep(self.interval_secs)

    def cancel(self):
        self.cancelled = True

if __name__=="__main__":
    main()

