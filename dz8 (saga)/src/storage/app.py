import json
import psycopg2
import os
import pika
import threading
from psycopg2.extras import RealDictCursor

def execute(query, comm: bool):
    conn = psycopg2.connect('')
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(query)
    if comm:
        conn.commit() 
    else:
        result = cursor.fetchone()
        cursor.close()
        return result
    conn.close()

properties = pika.BasicProperties(
    content_type='application/json',
    content_encoding='utf-8'
    )

credentials = pika.PlainCredentials(os.environ.get('RMQ_LOGIN', "guest"), os.environ.get('RMQ_PASS', "guest"))
parameters = pika.ConnectionParameters(os.environ.get('RMQ_HOSTNAME', "localhost"),
                                    5672,
                                    '/',
                                    credentials)

def listenStorage():
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    def callback(ch, method, properties, body):
        body = json.loads(body.decode())
        print(f"Пришло сообщение: {body}")
        cnt = f"""select COALESCE(sum(cnt),0) as sum from storage.products where product = '{body['product']}' """
        available = execute(cnt,False)
        print(f"Кол-во товара: {available['sum']}")
      
        if body['count'] > available['sum']:
            body['status'] = "NOOK"
            body['text'] = "Товара нет в наличии"
            channel.queue_declare(queue="storage_resault",durable=True)
            channel.basic_publish(exchange='',
                routing_key='storage_resault',
                properties=properties,
                body=json.dumps(body,ensure_ascii = False))
        else:
            new = f"""insert into storage.products(tr_guid, product, cnt) values ('{body['guid']}', '{body['product']}', 0-{body['count']})"""
            execute(new, True)
            channel.queue_declare(queue="delivery",durable=True)
            channel.basic_publish(exchange='',
                routing_key='delivery',
                properties=properties,
                body=json.dumps(body,ensure_ascii = False))

    channel.queue_declare(queue="storage",durable=True)
    channel.basic_consume(queue="storage", on_message_callback=callback, auto_ack=True)

    print('Начинаем слушать очередь storage')
    channel.start_consuming()

def listenResault():
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    def callback(ch, method, properties, body):
        body = json.loads(body.decode())
        print(f"Пришло сообщение: {body}")
        if body['status'] == 'NOOK':
            revert = f"""insert into storage.products(tr_guid, product, cnt) values ('{body['guid']}', '{body['product']}', {body['count']}) """
            execute(revert, True)

        channel.queue_declare(queue="storage_resault",durable=True)
        channel.basic_publish(exchange='',
            routing_key='storage_resault',
            properties=properties,
            body=json.dumps(body,ensure_ascii = False))

    channel.queue_declare(queue="delivery_resault",durable=True)
    channel.basic_consume(queue="delivery_resault", on_message_callback=callback, auto_ack=True)

    print('Начинаем слушать очередь delivery_resault')
    channel.start_consuming()

def dep():
    t1 = threading.Thread(target=listenStorage)
    t2 = threading.Thread(target=listenResault)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

app = dep()
