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

BLEADDR_PROFILE_ID = 'ySYH83QLG2'
BLEADDR_POST_ADDR = 'http://gatd.eecs.umich.edu:8081/' + BLEADDR_PROFILE_ID
WEARABOUTS_PROFILE_ID = '62MTxDGPhJ'
WEARABOUTS_POST_ADDR = 'http://gatd.eecs.umich.edu:8081/' + WEARABOUTS_PROFILE_ID

def main( ):

    # setup logging
    log = logging.getLogger('forwarder_log')
    log.setLevel(logging.DEBUG)
    log_filename = '../logs/experimental_forwarder_log.out'
    handler = logging.handlers.TimedRotatingFileHandler(log_filename,
            when='midnight', backupCount=7)
    log.addHandler(handler)
    log.info("Running forwarder...")
    print("Running forwarder...")

    # start threads to receive data from RabbitMQ
    bleAddr_queue = Queue.Queue()
    wearabouts_queue = Queue.Queue()
    threads = []
    threads.append(RabbitMQReceiverThread('experimental.scanner.bleScanner.#', 'bleAddr', bleAddr_queue, log))
    threads.append(RabbitMQReceiverThread('experimental.wearabouts.#', 'wearabouts', wearabouts_queue, log))
    threads.append(GATDPoster(BLEADDR_POST_ADDR, bleAddr_queue, log))
    threads.append(GATDPoster(WEARABOUTS_POST_ADDR, wearabouts_queue, log))

    while True:
        for thread in threads:
            if thread and not thread.isAlive():
                log.error(curr_datetime() + "ERROR - thread died")
                sys.exit(1)

        # only bother checking every ten seconds
        time.sleep(10)


def curr_datetime():
    return time.strftime("%m/%d/%Y %H:%M:%S ")


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

        self.recv_count = 0

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
                self.log.error(curr_datetime() + "ERROR - RabbitMQReceiver: " + str(e) + repr(e))

    def _on_data(self, channel, method, prop, body):
        # data received from rabbitmq. Push to msg_queue
        #print("RabbitMQ got data: " + str(body))
        self.recv_count += 1
        if self.recv_count%10000 == 0:
            self.log.info(curr_datetime() + "INFO - RabbitMQReceiver: Receive count = " + str(self.recv_count))

        self.message_queue.put([self.data_type, json.loads(body)])


class GATDPoster(Thread):
    def __init__(self, address, queue, log=None):
        # init thread
        super(GATDPoster, self).__init__()
        self.daemon = True

        # init data
        self.post_address = address
        self.msg_queue = queue
        self.log = log

        self.post_count = 0

        # autostart thread
        self.start()

    def run(self):
        while True:
            # look for a packet
            #Note: this line was edited to allow a Receiver to dump right into a Poster
            data = self.msg_queue.get()[1]
            #print("GATD posting data: " + str(data))
            data['experimental'] = True

            self.post_count += 1
            if self.post_count%1000 == 0:
                self.log.info(curr_datetime() + "INFO - GATDPoster: Post count = " + str(self.post_count))

            # post to GATD
            try:
                req = urllib2.Request(self.post_address)
                req.add_header('Content-Type', 'application/json')
                response = urllib2.urlopen(req, json.dumps(data))
            except Exception as e:
                # ignore error and carry on
                if self.log:
                    self.log.error(curr_datetime() + "ERROR - GATDPoster: " + str(e))
                else:
                    print(curr_datetime() + "ERROR - GATDPoster: " + str(e))
            finally:
                self.msg_queue.task_done()


if __name__=="__main__":
    main()

