#!/usr/bin/env python2

# This program is meant to be run from a BeagleBone Black attached to a
#   Sparkfun RFID reader on UART1

import sys
import serial
import time
import pika
from threading import Thread
import Queue
import json
import traceback

import logging
import logging.handlers

try:
    import config
except ImportError:
    print('Cannot find config file. Need symlink from shed')
    sys.exit(1)

# record reader mac address for determining location automatically
import subprocess
command = "ifconfig eth0 | grep HWaddr | cut -dH -f2 | cut -d\  -f2"
MAC_ADDRESS = subprocess.check_output(command, shell=True)[0:-1].upper()
if MAC_ADDRESS == '':
    from uuid import getnode as get_mac
    MAC_ADDRESS = ':'.join(("%012X" % get_mac())[i:i+2] for i in range(0, 12, 2))
    if MAC_ADDRESS == '':
        print('Cannot determine device MAC address')
        sys.exit(1)


def main():

    # setup logging
    log = logging.getLogger('rfidReader_log')
    log.setLevel(logging.DEBUG)
    log_filename = '../logs/experimental_rfidReader_log.out'
    handler = logging.handlers.TimedRotatingFileHandler(log_filename,
            when='midnight', backupCount=7)
    log.addHandler(handler)
    log.info("Running rfid reader...")
    print("Running rfid reader...")

    # open RFID read across UART
    ser = None
    try:
        # 9600 buad with a 10 second timeout on reads
        ser = serial.Serial(port="/dev/ttyO1", baudrate=9600, timeout=10)
    except serial.serialutil.SerialException:
        try:
            # backup is plugged in through USB directly
            ser = serial.Serial(port="/dev/ttyUSB0", baudrate=9600, timeout=10)
        except serial.serialutil.SerialException:
            print(curr_datetime() + "ERROR - UART port does not exist")
            log.error(curr_datetime() + "ERROR - UART port does not exist")
            sys.exit(1)

    # check that the serial port is valid
    ser.close()
    ser.open()
    if not ser.isOpen():
        print(curr_datetime() + "ERROR - Serial port could not be opened")
        log.error(curr_datetime() + "ERROR - Serial port could not be opened")
        sys.exit(1)

    # create RabbitMQ posting thread
    post_queue = Queue.Queue()
    threads = []
    threads.append(RabbitMQPoster('experimental.rfid.id_str', post_queue, log=log))

    # start RFID reader
    reader = RFIDReader(ser, post_queue, threads, log)
    while True:
        try:
            reader.run()
        except Exception as e:
            print(curr_datetime() + "ERROR - RFIDReader: " + str(e))
            log.error(curr_datetime() + "ERROR - RFIDReader: " + str(e))
            log.error(traceback.format_exc())


class RFIDReader ():

    def __init__(self, ser, post_queue, threads, log):
        self.ser = ser
        self.post_queue = post_queue
        self.threads = threads
        self.log = log

        global MAC_ADDRESS
        self.mac_address = MAC_ADDRESS

    def run(self):
        while True:
            data = None
            data_bytes = []

            # grab data until an "end of packet" byte is received
            while not data or ord(data) != 0x03:
                data = None
                data = self.ser.read()

                # check that I/O threads haven't died
                for thread in self.threads:
                    if thread and not thread.isAlive():
                        print(curr_datetime() + "ERROR - I/O thread died")
                        self.log.error(curr_datetime() + "ERROR - I/O thread died")
                        sys.exit(1)

                if data  == None or data == '':
                    continue

                data_bytes.append(data)

            # check data for validity
            if (len(data_bytes) == 16 and ord(data_bytes[0]) == 0x02 and
                    ord(data_bytes[13]) == 0x0D and ord(data_bytes[14]) == 0x0A and
                    ord(data_bytes[15]) == 0x03):

                id_str = ''.join(data_bytes[1:11])
                print(curr_datetime() + "Received id: " + str(id_str))
                self.log.debug(curr_datetime() + "Received id: " + str(id_str))

                packet = {}
                packet['timestamp'] = time.time()
                packet['id_str'] = id_str
                packet['location_str'] = 'unknown'
                packet['reader_macAddr'] = self.mac_address
                self.post_queue.put((packet, ''))
                
            else:
                self.log.error(curr_datetime() + "ERROR - Bad packet data: " + str(data_bytes))
                print(curr_datetime() + "ERROR - Bad packet data: " + str(data_bytes))

    def test(self):
        pass

def curr_datetime():
    return time.strftime("%m/%d/%Y %H:%M:%S ")

class RabbitMQPoster(Thread):
    def __init__(self, route_key, queue, log=None):

        # init thread
        super(RabbitMQPoster, self).__init__()
        self.daemon = True

        # init data
        self.route_key = route_key
        self.msg_queue = queue
        self.log = log

        # autostart thread
        self.start()

    def _open_connection(self):
        # Get a blocking connection to the rabbitmq
        self.amqp_conn = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=config.rabbitmq['host'],
                    virtual_host=config.rabbitmq['vhost'],
                    credentials=pika.PlainCredentials(
                        config.rabbitmq['login'],
                        config.rabbitmq['password']))
            )
        self.amqp_chan = self.amqp_conn.channel()


    def run(self):
        # open connection before starting
        self._open_connection()

        while True:
            # look for a packet
            (data, route) = self.msg_queue.get()

            # post to RabbitMQ
            try:
                self.amqp_chan.basic_publish(exchange=config.rabbitmq['exchange'],
                        body=json.dumps(data),
                        routing_key=self.route_key+'.'+route.replace(' ', '_').replace('|', '.'))
            except Exception as e:
                # Catch exception. Re-open. Try again
                self._open_connection()
                self.amqp_chan.basic_publish(exchange=config.rabbitmq['exchange'],
                        body=json.dumps(data),
                        routing_key=self.route_key+'.'+route.replace(' ', '_').replace('|', '.'))

            self.msg_queue.task_done()


if __name__=="__main__":
    main()

