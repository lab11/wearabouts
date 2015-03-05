#!/usr/bin/env python

from __future__ import print_function

import sys

try:
	import sh
except:
	print("Could not find the sh module:")
	print("  sudo pip install sh")
	sys.exit(1)

from sh import ln
from sh import rm
from sh import docker


DOCKERFILES = [
	('bleScannerHCI', 'lab11/wearabouts-ble-scanner-js'),
	('bleScanner', 'lab11/wearabouts-ble-scanner-py')
]


# Get rid of the Dockerfile in the root
print('Removing existing Dockerfile if it exists')
rm('Dockerfile', '-f')

# Build each docker image
for dockerfile in DOCKERFILES:
	print('Building {}'.format(dockerfile[1]))
	ln('-s', dockerfile[0]+'/Dockerfile', 'Dockerfile')
	for chunk in docker('build', '-t', 'lab11/wearabouts-ble-scanner-js', '.'):
		print(chunk, end="")

	rm('Dockerfile')
