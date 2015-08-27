#!/usr/bin/env python2

import json
import sys
from threading import Thread
import Queue
import time
import pika
import os

import logging
import logging.handlers

try:
    import config
except ImportError:
    print('Cannot find config file. Need symlink from shed')
    sys.exit(1)

try:
    import rfid_config
except ImportError:
    print('Cannot find rfid config file. Need symlink from shed')
    sys.exit(1)
# create a known-case dict of reader mac addresses
rfid_config.uppercase_readers = dict((k.upper(), v) for k,v in rfid_config.rfid_readers.iteritems())
rfid_config.uppercase_users   = dict((k.upper(), v) for k,v in rfid_config.rfid_cards.iteritems())

def main( ):

    # setup logging
    log = logging.getLogger('rfid_groundTruth_log')
    log.setLevel(logging.DEBUG)
    log_filename = '../logs/experimental_rfid_groundTruth_log.out'
    handler = logging.handlers.TimedRotatingFileHandler(log_filename,
            when='midnight', backupCount=7)
    log.addHandler(handler)
    #stdout_handler = logging.StreamHandler(sys.stdout)
    #log.addHandler(stdout_handler)
    log.info("Running RFID ground truth...")

    # start threads to receive data from GATD or RabbitMQ
    recv_queue = Queue.Queue()
    post_queue = Queue.Queue()
    threads = []
    threads.append(RabbitMQReceiverThread('experimental.rfid.id_str.#', 'rfid', recv_queue, log))
    threads.append(RabbitMQReceiverThread('experimental.rfid.control.#', 'control', recv_queue, log))
    threads.append(RabbitMQPoster('experimental.event.ground_truth', post_queue, log=log))

    # start ground truth
    truth = GroundTruth(recv_queue, post_queue, threads, log)
    #XXX: bring this back once it works
    #while True:
    #    try:
    #        generator.run()
    #    except Exception as e:
    #        log.error(curr_datetime() + "ERROR - EventGenerator: " + str(e))
    truth.run()

def curr_datetime():
    return time.strftime("%m/%d/%Y %H:%M:%S ")


class GroundTruth ():

    def __init__(self, recv_queue, post_queue, threads, log):
        self.recv_queue = recv_queue
        self.post_queue = post_queue
        self.threads = threads
        self.log = log

        self.rooms = {}
        self.people = {}
        self.last_update = 0
        self.last_data = 0
        self.start_time = time.time()

    def run(self):
        while True:

            data_type = 'None'
            pkt = None
            try:
                # wait for data
                [data_type, pkt] = self.recv_queue.get(timeout=5)
            except Queue.Empty:
                # No data has been seen, timeout occurred
                self.update_screen()

            # Check that I/O threads haven't died
            for thread in self.threads:
                if thread and not thread.isAlive():
                    self.log.error(curr_datetime() + "ERROR - I/O thread died")
                    sys.exit(1)

            # allow control signals to override possible errors
            if data_type == 'control':

                # control packets always good
                self.last_data = time.time()

                # add a new room if necessary
                if pkt['location_str'] != 'None' and pkt['location_str'] not in self.rooms:
                    self.rooms[pkt['location_str']] = []
                location = self.rooms[pkt['location_str']]

                # add a new person if necessary
                if pkt['uniqname'] != 'None' and pkt['uniqname'] not in self.people:
                    self.people[pkt['uniqname']] = {
                            'location_id': -1,
                            'location_str': 'None',
                            'full_name': pkt['full_name']
                            }

                if pkt['command'] == 'add':
                    for room in self.rooms:
                        if pkt['uniqname'] in self.rooms[room]:
                            self.rooms[room].remove(pkt['uniqname'])
                    location.append(pkt['uniqname'])
                    person = self.people[pkt['uniqname']]
                    person['location_str'] = pkt['location_str']
                    person['location_id'] = pkt['location_id']

                elif pkt['command'] == 'remove':
                    if pkt['uniqname'] in location:
                        location.remove(pkt['uniqname'])
                        person = self.people[pkt['uniqname']]
                        person['location_str'] = 'None'
                        person['location_id'] = -1

                elif pkt['command'] == 'empty':
                    self.rooms[pkt['location_str']] = []
                    for name in self.people:
                        if self.people[name]['location_str'] == pkt['location_str']:
                            self.people[name]['location_str'] = 'None'
                            self.people[name]['location_id'] = -1

                # transmit data
                post_data = {}
                post_data['timestamp'] = time.time()
                post_data['rooms'] = self.rooms.copy()
                post_data['people'] = self.people.copy()
                self.post_queue.put((post_data, 'rfid'))
                self.update_screen()
                continue

            # all other packets should be RFID readings
            if (data_type != 'rfid' or pkt == None or
                    'location_str' not in pkt or 'reader_macAddr' not in pkt or
                    'id_str' not in pkt or 'timestamp' not in pkt):
                continue

            # identify reader location
            if pkt['location_str'] == 'unknown':
                if pkt['reader_macAddr'].upper() in rfid_config.uppercase_readers:
                    pkt['location_str'] = rfid_config.uppercase_readers[pkt['reader_macAddr'].upper()][0]
                    pkt['location_id'] = rfid_config.uppercase_readers[pkt['reader_macAddr'].upper()][1]
                else:
                    self.log.debug(curr_datetime() + "Unknown reader sending data: " + str(pkt))
                    continue

            # determine user identity
            if pkt['id_str'].upper() in rfid_config.uppercase_users:
                pkt['uniqname'] = rfid_config.uppercase_users[pkt['id_str'].upper()][0]
                pkt['full_name'] = rfid_config.uppercase_users[pkt['id_str'].upper()][1]
            else:
                self.log.debug(curr_datetime() + "Unknown RFID card scanned: " + str(pkt))
                continue

            # packet good
            self.last_data = time.time()

            # add a new room if necessary
            if pkt['location_str'] not in self.rooms:
                self.rooms[pkt['location_str']] = []

            # add a new person if necessary
            if pkt['uniqname'] not in self.people:
                self.people[pkt['uniqname']] = {
                        'location_id': -1,
                        'location_str': 'None',
                        'full_name': pkt['full_name']
                        }

            location = self.rooms[pkt['location_str']]
            person = self.people[pkt['uniqname']]

            # check if individual is in room
            if pkt['uniqname'] in location:
                # remove person
                location.remove(pkt['uniqname'])
                person['location_id'] = -1
                person['location_str'] = 'None'
            else:
                # remove person from other rooms
                for loc in self.rooms.keys():
                    if pkt['uniqname'] in self.rooms[loc]:
                        self.rooms[loc].remove(pkt['uniqname'])
                        self.log.debug(curr_datetime() + "Had to remove " +
                                str(pkt['uniqname']) + " from " + str(loc))

                # add person to this room
                location.append(pkt['uniqname'])
                person['location_id'] = pkt['location_id']
                person['location_str'] = pkt['location_str']

            # transmit data
            post_data = {}
            post_data['timestamp'] = time.time()
            post_data['rooms'] = self.rooms.copy()
            post_data['people'] = self.people.copy()
            self.post_queue.put((post_data, 'rfid'))
            self.update_screen()

    def update_screen(self):
        # update as fast as possible. Packets don't come in that fast anyways
        if True or (time.time() - self.last_update) > 1:
            self.last_update = time.time()

            # clear terminal screen
            os.system('cls' if os.name == 'nt' else 'clear')
            print("Time: " + time.strftime("%I:%M:%S") +
                    '\t\t\tLast data ' + str(int(round(time.time() - self.last_data))) + 
                    ' seconds ago' +
                    '\t\tStarted ' + str(int(round(time.time() - self.start_time))) +
                    ' seconds ago')

            # print room data
            for room in self.rooms:
                room_name = room.split('|')[-1]
                print(room_name + ': ' + ' '.join(self.rooms[room]))


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

