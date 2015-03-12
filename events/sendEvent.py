#!/usr/bin/env python3

import sys
import os
import json
import pika

# get config file
CONFIG_PATH = os.path.expanduser('~/shed/projects/wearabouts/config.json')
config = {}
try:
    with open(CONFIG_PATH, 'r') as f:
        config = json.loads(f.read())
except ImportError:
    print('Cannot find config file!')
    sys.exit(1)

def post_to_RabbitMQ(data, route_key):

    # Get a blocking connection to the rabbitmq
    amqp_conn = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=config['host'],
                virtual_host=config['vhost'],
                credentials=pika.PlainCredentials(
                    config['login'],
                    config['password']))
        )
    amqp_chan = amqp_conn.channel()

    # post to RabbitMQ
    amqp_chan.basic_publish(exchange=config['exchange'],
                        body=json.dumps(data),
                        routing_key=route_key)

    # cleanup
    amqp_chan.close()


if len(sys.argv) != 3:
    print("./sendEvent.py MESSAGE ROUTE")

if __name__=="__main__":
    post_to_RabbitMQ(sys.argv[1], sys.argv[2])

