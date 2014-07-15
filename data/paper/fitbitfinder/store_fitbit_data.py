#!/usr/bin/env python

import IPy
import json
import sys
import time

try:
	import socketIO_client as sioc
except ImportError:
	print('Could not import the socket.io client library.')
	print('sudo pip install socketIO-client')
	sys.exit(1)

import logging
logging.basicConfig()

SOCKETIO_HOST      = 'inductor.eecs.umich.edu'
SOCKETIO_PORT      = 8083
SOCKETIO_NAMESPACE = 'stream'

query = {'profile_id': 'dwgY2s6mEu'}
query['time'] = 365*24*3600*1000

class stream_receiver (sioc.BaseNamespace):

    def on_reconnect (self):
        if 'time' in query:
                del query['time']
        stream_namespace.emit('query', query)

    def on_connect (self):
        stream_namespace.emit('query', query)

    def on_data (self, *args):
        process(args[0])

file_dict = {}
last_sample = 0

def process(pkt):
    global last_sample, file_dict

    if 'time' not in pkt:
        return
    if (time.time() - last_sample) > 10:
        last_sample = time.time()
        print("At time: " + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(pkt['time']/1000)))

    # need to determine whether this should be added to data file
    if 'location_str' not in pkt:
        print(pkt)
        exit()
        return

    # Note: I don't require a name for ble devices, because there are far less around,
    #   and a much smaller chance of an unlabeled one residing in our lab
    #if 'uniqname' not in pkt:
    #    return
    #if 'full_name' not in pkt:
    #    return

    # looks good. Create a file for it or clear existing file
    loc = pkt['location_str']
    if loc not in file_dict:
        filename = str(loc[-4:]) + '.data'
        file_obj = open(filename, 'w')
        file_dict[loc] = file_obj
        print("New file: " + filename)

    # write it down based on location
    file_dict[loc].write(str(pkt) + '\n')


if True:
    socketIO = sioc.SocketIO(SOCKETIO_HOST, SOCKETIO_PORT)
    stream_namespace = socketIO.define(stream_receiver,
	    '/{}'.format(SOCKETIO_NAMESPACE))

    socketIO.wait()
else:
    import GatdDataExtractor

    query = {"profile_id": "dwgY2s6mEu"}
    gde = GatdDataExtractor.GatdDataExtractor()
    data = gde.extract(parameters=query)
    for row in data:
        process(row)
