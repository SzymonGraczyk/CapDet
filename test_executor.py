import json
import pika
import uuid

def execute_test(host_ip, test_script):
    body = json.dumps(test_script)

    connection = pika.BlockingConnection(pika.ConnectionParameters(host=host_ip))

    channel = connection.channel(channel_number=2)
    channel.exchange_declare(exchange      = 'tests',
                             exchange_type = 'direct')

#    callback_queue = 'tests_queue'
    res = channel.queue_declare(exclusive=False)
    callback_queue = result.method.queue

    print res

    corr_id = str(uuid.uuid4())
    channel.basic_publish(exchange='tests',
                          routing_key='1',
                          properties=pika.BasicProperties(
                              reply_to = callback_queue,
                              correlation_id = corr_id,
                              content_type = 'application/json',
                          ),
                          body=str(body))

    connection.close()

    print 'execute_test done'
