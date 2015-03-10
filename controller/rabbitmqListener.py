
import pika
import time

try:
    import config
except ImportError:
    print('Need symlink for config from shed')
    sys.exit(1)

amqp_channel = None
queue_name = None

def curr_datetime():
    return time.strftime("%m/%d/%Y %H:%M:%S ")

def callback (channel, method, prop, body):
	print(curr_datetime() + body)

def pika_on_queue_bind (amqp_method_frame):
	global amqp_channel, queue_name

	amqp_channel.basic_consume(callback, queue_name, no_ack=True)


def pika_on_queue_declared (amqp_method_frame):
	global amqp_channel, queue_name

	queue_name = amqp_method_frame.method.queue
	print(queue_name)

	#route_key = 'scanner.#'
        #route_key = 'wearabouts'
        route_key = 'event.presence.#'

	amqp_channel.queue_bind(pika_on_queue_bind,
	                        exchange=config.rabbitmq['exchange'],
	                        queue=queue_name,
	                        routing_key=route_key)

# Setup the connection to RabbitMQ
def pika_on_channel (amqp_chan):
	global amqp_channel
	amqp_channel = amqp_chan

	amqp_channel.queue_declare(pika_on_queue_declared, exclusive=True)

def pika_on_connection (unused_connection):
	amqp_conn.channel(pika_on_channel)

amqp_conn = pika.SelectConnection(
				pika.ConnectionParameters(
					host=config.rabbitmq['host'],
					virtual_host=config.rabbitmq['vhost'],
					credentials=pika.PlainCredentials(
						config.rabbitmq['login'],
						config.rabbitmq['password'])),
				pika_on_connection
			)
amqp_conn.ioloop.start()
