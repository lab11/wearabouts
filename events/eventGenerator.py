#!/usr/bin/env python2

import IPy
import json
import sys
from threading import Thread
import Queue
import time
import random
import os
import urllib2
import pika
import argparse

import logging
import logging.handlers

try:
    import socketIO_client as sioc
except ImportError:
    print('Could not import the socket.io client library.')
    print('sudo pip install socketIO-client')
    sys.exit(1)


def main( ):

    # argument parsing
    parser = argparse.ArgumentParser(description='Determine locations of individuals based on BLE scan information.')
    parser.add_argument('-rabbit', '--rabbit',
            help='Pipe data from and results to a RabbitMQ instance. Specified in config.py', action='store_true')
    args = parser.parse_args()

    USE_RABBITMQ = False
    if args.rabbit:
        USE_RABBITMQ = True

    # setup logging
    log = logging.getLogger('eventGenerator_log')
    log.setLevel(logging.DEBUG)
    log_filename = '../logs/eventGenerator_log.out'
    handler = logging.handlers.TimedRotatingFileHandler(log_filename,
            when='midnight', backupCount=7)
    log.addHandler(handler)
    log.info("Running event generator...")
    print("Running event generator...")

    # start threads to receive data from GATD or RabbitMQ
    recv_queue = Queue.Queue()
    post_queue = Queue.Queue()
    threads = []
    if USE_RABBITMQ:
        threads.append(RabbitMQReceiverThread('wearabouts', 'wearabouts', recv_queue, log))
        threads.append(RabbitMQPoster('event.presence', post_queue, log=log))
    else:
        print("Events not supported in GATD currently. Run with --rabbit")
        sys.exit(1)

    # start event generator
    generator = EventGenerator(recv_queue, post_queue, threads, log)
    #XXX: bring this back once it works
    #while True:
    #    try:
    #        generator.run()
    #    except Exception as e:
    #        log.error(curr_datetime() + "ERROR - EventGenerator: " + str(e))
    generator.run()

def curr_datetime():
    return time.strftime("%m/%d/%Y %H:%M:%S ")


class EventGenerator ():

    def __init__(self, recv_queue, post_queue, threads, log):
        self.recv_queue = recv_queue
        self.post_queue = post_queue
        self.threads = threads
        self.log = log

        self.people = {}
        self.rooms = {}

    def run(self):
        while True:

            data_type = 'None'
            pkt = None
            try:
                # wait for data
                [data_type, pkt] = self.recv_queue.get(timeout=5)
            except Queue.Empty:
                # No data has been seen, timeout occurred
                pass

            # check that I/O threads haven't died
            for thread in self.threads:
                if thread and not thread.isAlive():
                    self.log.error(curr_datetime() + "ERROR - I/O thread died")
                    sys.exit(1)

            if (pkt == None or 'location_str' not in pkt or 'type' not in pkt):
                continue

            event_list = []
            event_pkt = {}
            location_str = pkt['location_str']
            if 'type' in pkt and pkt['type'] == 'person':
                # copy over some parameters into event in case they are useful
                #event_pkt['uniqname'] = pkt['uniqname']
                #event_pkt['full_name'] = pkt['full_name']
                #event_pkt['present_since'] = pkt['present_since']
                #event_pkt['last_seen'] = pkt['last_seen']
                #event_pkt['confidence'] = pkt['confidence']
                #event_pkt['present_by'] = pkt['present_by']

                uniqname = pkt['uniqname']
                # create new person if necessary
                if uniqname not in self.people:
                    self.people[uniqname] = 'None'

                # create events
                if self.people[uniqname] == 'None' and location_str != 'None':
                    event_pkt['location_str'] = location_str
                    event_pkt['event_str'] = uniqname + ' in location'
                    event_list.append(event_pkt)
                elif location_str == 'None' and self.people[uniqname] != 'None':
                    event_pkt['location_str'] = self.people[uniqname]
                    event_pkt['event_str'] = uniqname + ' not in location'
                    event_list.append(event_pkt)
                elif self.people[uniqname] != location_str:
                    event_pkt1 = event_pkt.copy()
                    event_pkt1['location_str'] = self.people[uniqname]
                    event_pkt1['event_str'] = uniqname + ' not in location'
                    event_list.append(event_pkt1)
                    event_pkt2 = event_pkt
                    event_pkt2['location_str'] = location_str
                    event_pkt2['event_str'] = uniqname + ' in location'
                    event_list.append(event_pkt2)

                self.people[uniqname] = location_str

            elif 'type' in pkt and pkt['type'] == 'room':
                # copy over some parameters into event in case they are useful
                #event_pkt['person_list'] = pkt['person_list']
                #event_pkt['since_list'] = pkt['since_list']

                # create new room if necessary
                if location_str != 'None' and location_str not in self.rooms:
                    self.rooms[location_str] = None

                isOccupied = (len(pkt['person_list']) > 0)
                if self.rooms[location_str] != isOccupied:
                    if isOccupied:
                        event_pkt['location_str'] = location_str
                        event_pkt['event_str'] = 'Location occupied'
                        event_list.append(event_pkt)
                    else:
                        event_pkt['location_str'] = location_str
                        event_pkt['event_str'] = 'Location not occupied'
                        event_list.append(event_pkt)

                self.rooms[location_str] = isOccupied

            else:
                self.log.error(curr_datetime() + "ERROR - Received invalid packet " + str(pkt))
                continue

            # post events to queue if any
            if len(event_list) > 0:
                for event in event_list:
                    self.log.debug(curr_datetime() + "DEBUG - " + str(event))
                    print(curr_datetime() + event['event_str'] + ' at ' + event['location_str'])
                    self.post_queue.put((event, event['location_str']))


class RabbitMQReceiverThread (Thread):

    def __init__(self, route_key, data_type, message_queue, log):
        # init thread
        super(RabbitMQReceiverThread, self).__init__()
        self.daemon = True

        # init data
        self.route_key = route_key
        self.data_type = data_type
        self.message_queue = message_queue
        self.log = log

        # start thread
        print("Running thread")
        self.start()


    def run(self):
        try:
            import config
        except ImportError:
            print('Cannot find config file. Need symlink from shed')
            sys.exit(1)

        while True:
            try:
                amqp_conn = pika.BlockingConnection(
                        pika.ConnectionParameters(
                            host = config.rabbitmq['host'],
                            virtual_host=config.rabbitmq['vhost'],
                            credentials=pika.PlainCredentials(
                                config.rabbitmq['login'],
                                config.rabbitmq['password'])))

                amqp_chan = amqp_conn.channel()

                result = amqp_chan.queue_declare(exclusive=True)

                queue_name = result.method.queue
                amqp_chan.queue_bind(
                        exchange=config.rabbitmq['exchange'],
                        queue = queue_name,
                        routing_key = self.route_key)

                amqp_chan.basic_consume(self._on_data, queue_name, no_ack=True)

                amqp_chan.start_consuming()
            except Exception as e:
                self.log.error(curr_datetime() + "ERROR - RabbitMQReceiver: " + str(e))

    def _on_data(self, channel, method, prop, body):
        # data received from rabbitmq. Push to msg_queue
        self.message_queue.put([self.data_type, json.loads(body)])


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

    def run(self):
        try:
            import config
        except ImportError:
            print('Cannot find config file. Need symlink from shed')
            sys.exit(1)

        while True:
            try:
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

                while True:
                    # look for a packet
                    (data, route) = self.msg_queue.get()

                    # post to RabbitMQ
                    print("\tPosting to route: " + self.route_key+'.'+route.replace(' ', '_').replace('|', '.'))
                    self.amqp_chan.basic_publish(exchange=config.rabbitmq['exchange'],
                                        body=json.dumps(data),
                                        routing_key=self.route_key+'.'+route.replace(' ', '_').replace('|', '.'))

                    self.msg_queue.task_done()
            except Exception as e:
                self.log.error(curr_datetime() + "ERROR - RabbitMQPoster: " + str(e))


if __name__=="__main__":
    main()

