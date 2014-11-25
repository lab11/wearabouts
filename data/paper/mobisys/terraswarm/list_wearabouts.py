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

query = {'profile_id': '62MTxDGPhJ',
        'time': (time.time() - 1414573200000)}

pkts = {}


class stream_receiver (sioc.BaseNamespace):
	def on_reconnect (self):
		if 'time' in query:
			del query['time']
		stream_namespace.emit('query', query)

	def on_connect (self):
		stream_namespace.emit('query', query)

	def on_data (self, *args):
		pkt = args[0]
		print(pkt)


socketIO = sioc.SocketIO(SOCKETIO_HOST, SOCKETIO_PORT)
stream_namespace = socketIO.define(stream_receiver,
	'/{}'.format(SOCKETIO_NAMESPACE))

socketIO.wait()
