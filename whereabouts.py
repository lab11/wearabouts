#!/usr/bin/env python

import IPy
import json
import sys
import fitbitfinder

try:
    import socketIO_client as sioc
except ImportError:
    print('Could not import the socket.io client library.')
    print('sudo pip install socketIO-client')
    sys.exit(1)

import logging
logging.basicConfig()

SOCKETIO_HOST      = 'inductor.eecs.umich.edu'
SOCKETIO_PORT      = 8082
SOCKETIO_NAMESPACE = 'stream'

DEVICE_MAP_FILE = "device-map.json"
LOCATION = "" #Get this as a system argument
DOOR_TRIGGERED = None #Get this as a system argument

USAGE = """Please specify location being monitored.

Door sensors, while not necessary, are available in the following locations:"""


# gets deployment location, picks door-triggered or polling monitor
# depending on whether there is a door sensor available.
# it would be nice to generalize this trigger idea in the future.
def main():
    door_sensor_locations = get_door_sensor_locations()

    # get location
    if len(sys.argv) != 2:
        print(USAGE)
        print(door_sensor_locations)
    else:
        LOCATION = sys.argv[1]

    # if location has door sensor, trigger on it
    if LOCATION in door_sensor_locations:
        DOOR_TRIGGERED = True
    else:
        DOOR_TRIGGERED = False
    
    # door/gatd triggered logic
    if DOOR_TRIGGERED:
        # SET GATD QUERY TO PROPER DOOR SENSOR HERE
        socketIO = sioc.SocketIO(SOCKETIO_HOST, SOCKETIO_PORT)
        stream_namespace = socketIO.define(EventDrivenMigrationMonitor,
            '/{}'.format(SOCKETIO_NAMESPACE))
        socketIO.wait()
    # periodic polling logic
    else:
        pass
#       PollingMigrationMonitor(30*60) # poll every 30 mins

def get_door_sensor_locations():
    door_sensor_locations = []
    f = open(DEVICE_MAP_FILE)
    contents = f.read()
    f.close()
    contents = contents.replace("\n", "")
    contents = contents.replace("\t", "")
    device_maps = json.loads(contents)
    for device_map in device_maps:
        if device_map["descr"] == "door sensor":
            door_sensor_locations.append(device_map["location"])
    return door_sensor_locations    

def sanitize(device_id):
    return device_id.replace(":", "").upper()


# looks for migration sets after a door event occurs
class EventDrivenMigrationMonitor (sioc.BaseNamespace, MigrationMonitor):
    # CHANGE THIS TO DOOR OPEN/CLOSE EVENT QUERY
    query = {'profile_id': '7aiOPJapXF',
         '_processor_freq': 'last',
         'time': 500000}
    query = {}

    def on_reconnect (self):
        if 'time' in query:
            del query['time']
        stream_namespace.emit('query', query)

    def on_connect (self):
        stream_namespace.emit('query', query)

    # what if door is propped open?
    def on_data (self, *args):
        pkt = args[0]
        print(pkt)
        # if door open event:
            #self.update()


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


class MigrationMonitor(Object):
    last_seen_owners = []

    def update(self):
        # check for present fitbits.
        present_fitbits = fitbitfinder.discover_fitbits()
        # sanitize
        for i,fitbit in enumerate(present_fitbits):
            present_fitbits[i] = sanitize(fitbit)
        # match fitbit list against known list
        migrants = self.get_migrants(present_fitbits)
        # send these changes to gatd
        
    def get_migrants(self, present_fitbits):
        present_owners = self.get_owners(present_fitbits)
        if self.last_seen_owners != []:
            appeared = [p for p in present_owners if p not in self.last_seen_owners]
            disappeared = [p for p in self.last_seen_owners if p not in present_owners]
            #debug
            for p in appeared:
                print(str(p) + " has entered " + LOCATION)
            #debug
            for p in disappeared:
                print(str(p) + " has left " + LOCATION) 
        self.last_seen_owners = present_owners

    def get_owners(self, devices):
        owners = []
        f = open(DEVICE_MAP_FILE)
        contents = f.read()
        f.close()
        contents = contents.replace("\n", "")
        contents = contents.replace("\t", "")
        device_maps = json.loads(contents)
        for device_map in device_maps:
            if sanitize(device_map["device"]) in devices and device_map["owner"] not in people:
                people.append(device_map["owner"])
        return owners


if __name__=="__main__":
    main()

