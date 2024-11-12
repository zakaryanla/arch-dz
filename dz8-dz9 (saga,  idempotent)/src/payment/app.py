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
        cnt = f"""select COALESCE(sum(sum),0) as sum from payment.history where userid = '{body['user']}' """
        available = execute(cnt,False)
        print(f"Денег на счету: {available}")
        
        if body['sum'] > available['sum']:
            body['status'] = "NOOK"
            body['text'] = "Недостаточно средств"
            channel.queue_declare(queue="payment_resault",durable=True)
            channel.basic_publish(exchange='',
                routing_key='payment_resault',
                properties=properties,
                body=json.dumps(body,ensure_ascii = False))
        else:
            new = f"""insert into payment.history(tr_guid, userid, sum) values ('{body['guid']}', '{body['user']}', 0-{body['sum']})"""
            execute(new, True)
            body['status'] = "OK"
            body['text'] = "Успешно"
            channel.queue_declare(queue="payment_resault",durable=True)
            channel.basic_publish(exchange='',
                routing_key='payment_resault',
                properties=properties,
                body=json.dumps(body,ensure_ascii = False))

    channel.queue_declare(queue="payment",durable=True)
    channel.basic_consume(queue="payment", on_message_callback=callback, auto_ack=True)

    print('Начинаем слушать очередь payment')
    channel.start_consuming()

def dep():
    t1 = threading.Thread(target=listenStorage)
    t1.start()

app = dep()
    
