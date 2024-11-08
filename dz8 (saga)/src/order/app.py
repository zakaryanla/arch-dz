import json
import psycopg2
import os
import pika
import uuid
import threading
from flask import Flask,Response, request
from psycopg2.extras import RealDictCursor
from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics


def url(req):
    return '%s' % (req.url_rule)

app = Flask(__name__)
# metrics = GunicornPrometheusMetrics(app, group_by=url)

def userid():
    return request.headers.get('X-Auth-Request-User') 

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
    
# {"date": "2025-02-02", "product": "pizza", "count": 2, "sum": 100}
@app.route('/api/v1/order/buy', methods=['POST'])
def buy():
    data = request.get_json(force=True)

    print("Проверяем авторизацию")
    if not userid():
       return json.dumps({"message": "Отсутствует авторизация"},ensure_ascii = False)
    
    print(f"Авторизация есть: {userid()}")

    data["user"] = f"{userid()}"
    data["guid"] = str(uuid.uuid4())

    query_insert_history = f"insert into orderdb.history(userid, tr_guid, dt, cnt, product, sum, resault) values ('{data['user']}', '{data['guid']}', '{data['date']}',{data['count']}, '{data['product']}', {data['sum']}, 'created' ) "
    execute(query_insert_history, True)

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue="storage",durable=True)
    channel.basic_publish(exchange='',
                      routing_key='storage',
                      properties=properties,
                      body=json.dumps(data,ensure_ascii = False))
    connection.close()
    print("Отправлено сообщение в MQ")

    resp = {}
    resp['message'] = "Запрос успешно принят"
    resp['guid'] = data["guid"]
    return Response(json.dumps(resp,ensure_ascii = False), mimetype='application/json')

@app.route('/api/v1/order/buy/<guid>', methods=['GET'])
def get(guid):
    select = f"""select * from orderdb.history where tr_guid = '{guid}' """
    resp = execute(select, False)
    resp = json.dumps(resp, indent=4, sort_keys=True, default=str,ensure_ascii = False)
    print(resp)
    return Response(resp, mimetype='application/json')

def listenResault():
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    def callback(ch, method, properties, body):
        body = json.loads(body.decode())
        print(f"Пришло сообщение: {body}")
        update = f"""update orderdb.history set resault = '{body['text']}', status = '{body['status']}' where tr_guid = '{body['guid']}' """
        execute(update, True)

    channel.queue_declare(queue="storage_resault",durable=True)
    channel.basic_consume(queue="storage_resault", on_message_callback=callback, auto_ack=True)

    print('Начинаем слушать очередь storage_resault')
    channel.start_consuming()

t = threading.Thread(target=listenResault)
t.daemon = True
t.start()

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)