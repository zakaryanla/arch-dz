import json
import psycopg2
import requests
import os
import pika
from flask import Flask,Response, request
from psycopg2.extras import RealDictCursor
from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics


def url(req):
    return '%s' % (req.url_rule)

app = Flask(__name__)
metrics = GunicornPrometheusMetrics(app, group_by=url)

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

@app.route('/api/v1/order/buy', methods=['POST'])
def buy():
    data = request.get_json(force=True)

    print("Проверяем авторизацию")
    if not userid():
       return json.dumps({"message": "Отсутствует авторизация"},ensure_ascii = False)
    
    print(f"Авторизация есть: {userid()}")

    sum = 0 - data['sum']
    body = f"""{{"sum": {sum}}}"""
    r = requests.patch(os.environ.get('BILLING_URL', "http://127.0.0.1:2000/api/v1/billing/change"), headers={"X-Auth-Request-User":userid()}, data=body)

    resp = r.json()
    resp['product']= f"{data['product']}"

    query_insert_history = f"insert into orders.history(userid, product, sum, resault) values ('{userid()}', '{data['product']}', {data['sum']}, '{resp['status']}') "
    execute(query_insert_history, True)

    properties = pika.BasicProperties(
        content_type='application/json',
        content_encoding='utf-8'
        )

    credentials = pika.PlainCredentials(os.environ.get('RMQ_LOGIN', ""), os.environ.get('RMQ_PASS', ""))
    parameters = pika.ConnectionParameters(os.environ.get('RMQ_HOSTNAME', "localhost"),
                                        5672,
                                        '/',
                                        credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue="orders",durable=True)
    channel.basic_publish(exchange='',
                      routing_key='orders',
                      properties=properties,
                      body=json.dumps(resp,ensure_ascii = False))
    connection.close()
    print("Отправлено сообщение в MQ")
 
    return Response(json.dumps(resp,ensure_ascii = False), mimetype='application/json')

if __name__ == '__main__':
    app.run(host="0.0.0.0")