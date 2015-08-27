#!/usr/bin/env python2

import json
import sys
from threading import Thread
import Queue
import time
import pika
import os
import readline

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

    # start threads to receive data from GATD or RabbitMQ
    post_queue = Queue.Queue()
    threads = []
    threads.append(RabbitMQPoster('experimental.rfid.control', post_queue))

    # start commander
    commander = GroundTruthCommand(None, post_queue, threads, None)
    #XXX: bring this back once it works
    #while True:
    #    try:
    #        generator.run()
    #    except Exception as e:
    #        log.error(curr_datetime() + "ERROR - EventGenerator: " + str(e))
    commander.run()

def curr_datetime():
    return time.strftime("%m/%d/%Y %H:%M:%S ")


class GroundTruthCommand ():

    def __init__(self, recv_queue, post_queue, threads, log):
        self.recv_queue = recv_queue
        self.post_queue = post_queue
        self.threads = threads
        self.log = log

    def run(self):
        print("Ground Truth Commander!")

        while True:

            print("")
            print("Select command:")
            print("\t1) Empty")
            print("\t2) Add")
            print("\t3) Remove")
            select = raw_input("Enter a number: ")

            if not select.isdigit():
                continue
            select = int(select)
            if select < 1 or select > 3:
                continue

            command = "None"
            location_str = "None"
            location_id = '-1'
            uniqname = "None"
            full_name = "None"

            if select == 1:
                command = 'empty'
                print("")
                print("Empty a room")
                print("------------")
                room_num = raw_input("Enter a room number: ")
                location_str = 'University of Michigan|BBB|' + room_num
                for key,value in rfid_config.rfid_readers.iteritems():
                    if value[0] == location_str:
                        location_id = value[1]
                        break
                else:
                    print("Bad room number")
                    continue

            elif select == 2:
                command = 'add'
                print("")
                print("Add a uniqname")
                print("--------------")
                room_num = raw_input("Enter a room number: ")
                location_str = 'University of Michigan|BBB|' + room_num
                for key,value in rfid_config.rfid_readers.iteritems():
                    if value[0] == location_str:
                        location_id = value[1]
                        break
                else:
                    print("Bad room number")
                    continue

                uniqname = raw_input("Enter a uniqname: ")
                for key,value in rfid_config.rfid_cards.iteritems():
                    if value[0] == uniqname:
                        full_name = value[1]
                        break
                else:
                    print("Bad uniqname")
                    continue

            elif select == 3:
                command = 'remove'
                print("")
                print("Remove a uniqname")
                print("-----------------")
                room_num = raw_input("Enter a room number: ")
                location_str = 'University of Michigan|BBB|' + room_num
                for key,value in rfid_config.rfid_readers.iteritems():
                    if value[0] == location_str:
                        location_id = value[1]
                        break
                else:
                    print("Bad room number")
                    continue

                uniqname = raw_input("Enter a uniqname: ")
                for key,value in rfid_config.rfid_cards.iteritems():
                    if value[0] == uniqname:
                        full_name = value[1]
                        break
                else:
                    print("Bad uniqname")
                    continue

            else:
                print("CONFUSION")
                continue

            # transmit data
            post_data = {}
            post_data['timestamp'] = time.time()
            post_data['command'] = command
            post_data['location_str'] = location_str
            post_data['location_id'] = location_id
            post_data['uniqname'] = uniqname
            post_data['full_name'] = full_name
            self.post_queue.put((post_data, 'rfid'))


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

