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
        cnt = f"""select id as runner from delivery.runners r where not exists (select 1 from delivery.delivery where r.id = userid and slot = '{body['date']}' and state != 'cancelled') """
        available = execute(cnt,False)
        print(f"Свободные курьеры: {available}")

        if available:
            new = f"""insert into delivery.delivery(tr_guid, userid, slot, state) values ('{body['guid']}', {available['runner']}, '{body['date']}','reserve')"""
            execute(new, True)
            channel.queue_declare(queue="payment",durable=True)
            channel.basic_publish(exchange='',
                routing_key='payment',
                properties=properties,
                body=json.dumps(body,ensure_ascii = False))
        else:
            body['status'] = "NOOK"
            body['text'] = "Отсутствуют свободные курьеры на выбранную дату"
            channel.queue_declare(queue="delivery_resault",durable=True)
            channel.basic_publish(exchange='',
                routing_key='delivery_resault',
                properties=properties,
                body=json.dumps(body,ensure_ascii = False))

    channel.queue_declare(queue="delivery",durable=True)
    channel.basic_consume(queue="delivery", on_message_callback=callback, auto_ack=True)

    print('Начинаем слушать очередь delivery')
    channel.start_consuming()

def listenResault():
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    def callback(ch, method, properties, body):
        body = json.loads(body.decode())
        print(f"Пришло сообщение: {body}")
        if body['status'] == 'OK':
            new = f"""update delivery.delivery set state = 'сonfirmed' where tr_guid = '{body['guid']}' """
            execute(new, True)
        if body['status'] == 'NOOK':
            new = f"""update delivery.delivery set state = 'cancelled' where tr_guid = '{body['guid']}' """
            execute(new, True)
        channel.queue_declare(queue="delivery_resault",durable=True)
        channel.basic_publish(exchange='',
            routing_key='delivery_resault',
            properties=properties,
            body=json.dumps(body,ensure_ascii = False))


    channel.queue_declare(queue="payment_resault",durable=True)
    channel.basic_consume(queue="payment_resault", on_message_callback=callback, auto_ack=True)

    print('Начинаем слушать очередь payment_resault')
    channel.start_consuming()

def dep():
    t1 = threading.Thread(target=listenStorage)
    t2 = threading.Thread(target=listenResault)
    t1.start()
    t2.start()
    t1.join()
    t2.join()

app = dep()
