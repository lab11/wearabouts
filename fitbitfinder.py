#!/usr/bin/env python2

# Script to find fitbits
#   Finds Fitbit IDs and RSSI to the fitbit
#   Uploads data to GATD for use by other programs
#   Can also be called in TEST mode to determine fitbit IDs
#
# Uses Galileo for fitbit base station interactions
#   https://bitbucket.org/benallard/galileo

import sys
import uuid
from ctypes import c_byte

import IPy
import json
import sys
from threading import Thread, Lock
from time import sleep, strftime, time, localtime
import urllib2
import usb

try:
    import galileo.main
    import galileo.dongle
    import galileo.tracker
    import galileo.utils
except ImportError:
    print("Unable to find the Galileo Library")
    print("    sudo pip install galileo")
    exit()

try:
    import socketIO_client as sioc
except ImportError:
    print('Could not import the socket.io client library.')
    print('sudo pip install socketIO-client')
    sys.exit(1)

import logging
logging.basicConfig()

DOOR_GET_ADDR = 'http://inductor.eecs.umich.edu:8085/explore/profile/U8H29zqH0i'
FITBIT_POST_ADDR = 'http://inductor.eecs.umich.edu:8081/dwgY2s6mEu'

LOCATION = ""
query = {'profile_id': 'U8H29zqH0i',
        'location_str': None} #specified in main once location is known
stream_namespace = None

USAGE = """
To perform a one-time scan, specify 'test'

To perform continuous monitoring, please specify location being monitored.
If no door sensor is present at the specified location, the program defaults
to polling periodically.

Locations should be specified in the format:
    University|Building|Room

Door sensors are available in the following locations:"""

mutex = Lock()
last_discovery_time = 0

# gets deployment location, picks door-triggered or polling monitor
# depending on whether there is a door sensor available.
# it would be nice to generalize this trigger idea in the future.
def main():
    global LOCATION
    global stream_namespace
    global usage

    SOCKETIO_HOST      = 'inductor.eecs.umich.edu'
    SOCKETIO_PORT      = 8082
    SOCKETIO_NAMESPACE = 'stream'

    LOCATION = "" #Get this as a system argument
    DOOR_TRIGGERED = False #Get this as a system argument

    try:
        door_sensors = get_door_locations()
    except urllib2.URLError:
        print("Connection to inductor unavailable. Running in test mode")
        LOCATION = 'test'

    # get location
    if not LOCATION:
        if len(sys.argv) != 2:
            print(USAGE)
            index = 0
            for sensor_loc in door_sensors:
                print("    [" + str(index) + "]: " + sensor_loc)
                index += 1
            print("")
            user_input = raw_input("Select a location or enter a new one: ")

            if user_input.isdigit():
                user_input = int(user_input)
                if 0 <= user_input < index:
                    LOCATION = door_sensors[user_input]
                else:
                    print("Invalid selection")
                    exit()
            else:
                LOCATION = user_input
        else:
            LOCATION = sys.argv[1]

    if LOCATION == 'test':
        print('Scanning for fitbits...')
        test = FitbitMonitor()
        present_fitbits = test.get_present_fitbits()
        for key in present_fitbits.keys():
            print(str(key) + ' : ' + str(present_fitbits[key]))
        exit()

    print("Running fitbitfinder at " + LOCATION)

    # also start periodic polling
    print("\nStarting polling monitor")
    PollingMonitor(10*60) # poll every 10 mins + time to find devices

    # if location has door sensor, trigger on it as well
    for sensor_loc in door_sensors:
        if sensor_loc == LOCATION:
            DOOR_TRIGGERED = True
            query['location_str'] = LOCATION
    
    # door/gatd triggered logic
    if DOOR_TRIGGERED:
        print("\nStarting door-triggered monitor")
        socketIO = sioc.SocketIO(SOCKETIO_HOST, SOCKETIO_PORT)
        stream_namespace = socketIO.define(EventDrivenMonitor,
            '/{}'.format(SOCKETIO_NAMESPACE))
        socketIO.wait()

    # loop forever while polling and possibly door callbacks are occurring
    while(True):
        pass

def get_door_locations():

    # query GATD explorer to find door sensor locations
    req = urllib2.Request(DOOR_GET_ADDR)
    response = urllib2.urlopen(req)
    json_data = json.loads(response.read())

    if 'location_str' in json_data:
        return json_data['location_str'].keys()
    else:
        return ['None']

def sanitize(device_id):
    return device_id.replace(":", "").upper()

def cur_datetime(time_num):
    return strftime("%m/%d/%Y %H:%M", localtime(time_num/1000))

def post_to_gatd(fitbit_id, rssi):
    global LOCATION

    # Create standard data
    #TODO: Add a sequence number or maybe station id number in case mulitple
    #   fitbit finders are running in a single room
    if fitbit_id:
        data = {
                'location_str' : LOCATION,
                'fitbit_id' : fitbit_id,
                'rssi' : rssi
                }
    else:
        data = {
                'location_str' : LOCATION,
                'fitbit_id' : 'None'
                }

    # This is the post address for fitbitLocator
    print("starting post to GATD of" + str(json.dumps(data)))
    req = urllib2.Request(FITBIT_POST_ADDR)
    req.add_header('Content-Type', 'application/json')

    # Actually post to GATD
    response = urllib2.urlopen(req, json.dumps(data))
    print("POST complete")

class FitbitMonitor():

    def update(self):
        global mutex
        global last_discovery_time

        # take the mutex. This stops polling from conflicting with SocketIO
        mutex.acquire()

        # update discovery time
        last_discovery_time = time()

        # check for present fitbits
        present_fitbits = self.get_present_fitbits()

        # send data to GATD
        if present_fitbits:
            for key,value in present_fitbits.items():
                post_to_gatd(key, value)
        else:
            post_to_gatd(None, None)

        # give up the mutex
        mutex.release()

    def get_present_fitbits(self):
        present_fitbits = {}
        for i in range(3):
            fitbit_data = self.discover_fitbits()
            # if timeout, try again
            if fitbit_data == None:
                i = i-1
            # otherwise merge dicts, keeping original RSSI value
            else:
                present_fitbits = dict(fitbit_data.items() + present_fitbits.items())
        return present_fitbits

    # This function is nominally copied from galileo.main.syncAllTrackers()
    #   with many calls that we don't care about removed
    def discover_fitbits(self):
        dongle = galileo.dongle.FitBitDongle()
        try:
            dongle.setup()
        except galileo.dongle.NoDongleException:
            print("No fitbit base station connected, aborting")
            return
        except galileo.dongle.PermissionDeniedException:
            print(galileo.main.PERMISSION_DENIED_HELP)
            return

        try:
            fitbit = galileo.tracker.FitbitClient(dongle)
            fitbit.disconnect()
            fitbit.getDongleInfo()
            trackers = [t for t in self.discovery(dongle)]

        except galileo.dongle.TimeoutError:
            print("Timeout trying to discover trackers")
            return
        except usb.core.USBError:
            print("Darned USB Error. Let's try to keep going...")
            return
        except galileo.dongle.PermissionDeniedException:
            print(galileo.main.PERMISSION_DENIED_HELP)
            return

        return dict(trackers)

    # This function is essentially a rewritten version of
    #   galileo.tracker.discover() which only uses the parts we need
    def discovery(self, dongle):
        # control settings
        uuid = galileo.main.FitBitUUID
        service1 = 0xfb00
        write = 0xfb01
        read = 0xfb02
        minDuration = 4000

        # start discovery
        data = galileo.utils.i2lsba(uuid.int, 16)
        for i in (service1, write, read, minDuration):
            data += galileo.utils.i2lsba(i, 2)
        dongle.ctrl_write(galileo.dongle.CM(4, data))

        # find fitbits
        while True:
            d = dongle.ctrl_read(minDuration)
            if galileo.dongle.isStatus(d, 'StartDiscovery', False): continue
            elif d.INS == 2: break

            ID = sanitize(galileo.utils.a2x(d.payload[:6], ''))
            RSSI = c_byte(d.payload[7]).value
            yield [ID, RSSI]

        # stop discovery
        dongle.ctrl_write(galileo.dongle.CM(5))
        galileo.dongle.isStatus(dongle.ctrl_read(), 'CancelDiscovery')


# looks for fibit data after a door event occurs
class EventDrivenMonitor (sioc.BaseNamespace, FitbitMonitor):
    
    def on_reconnect (self):
        if 'time' in query:
            del query['time']
        stream_namespace.emit('query', query)

    def on_connect (self):
        stream_namespace.emit('query', query)

    def on_data (self, *args):
        pkt = args[0]
        msg_type = pkt['type']
        print(cur_datetime(pkt['time']) + ": " + pkt['type'].replace('_', ' ').capitalize() + " (" + str(LOCATION) + ")")
        # people entering or leaving. Check fitbits after a delay
        if msg_type == 'door_open':
            sleep(60)
            self.update()


# looks for fitbit events periodically 
# i.e., does not require a door sensor
class PollingMonitor(Thread, FitbitMonitor):

    def __init__(self, interval_secs):
        # thread stuff
        super(PollingMonitor, self).__init__()
        self.daemon = True
        self.cancelled = False
        # logic parameters
        self.interval_secs = interval_secs
        # gooooooooo
        self.start()

    def run(self):
        global last_discovery_time

        while not self.cancelled:
            if (time() - last_discovery_time) >= self.interval_secs:
                print("\nPolling {}".format(strftime("%Y-%m-%d %H:%M:%S")))
                self.update()
            else:
                print("\nPolling skipped due to recent sample")
            # Go back to sleep until the interval will have passed
            sleep(max(self.interval_secs - (time() - last_discovery_time), 0))
            

    def cancel(self):
        self.cancelled = True

if __name__ == "__main__":
    main()
