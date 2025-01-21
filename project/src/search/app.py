import json
import psycopg2
import os
import pika
import threading
from datetime import datetime
from elasticsearch import Elasticsearch
from flask import Flask,Response, request
from psycopg2.extras import RealDictCursor
from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics

class ListOfListsEncoder(json.JSONEncoder):
	def default(self, obj):
		if isinstance(obj, list):
			return obj
		return json.JSONEncoder.default(self, obj)
     
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

properties = pika.BasicProperties(
    content_type='application/json',
    content_encoding='utf-8'
    )

credentials = pika.PlainCredentials(os.environ.get('RMQ_LOGIN', "guest"), os.environ.get('RMQ_PASS', "guest"))
parameters = pika.ConnectionParameters(os.environ.get('RMQ_HOSTNAME', "localhost"),
                                    5672,
                                    '/',    
                                    credentials)
    
es = Elasticsearch(os.environ.get('ES_URL', "http://arch-es.homework:80/"))
index = 'lib'
res = es.indices.create(index=index, ignore=400)

def listen():
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    def callback(ch, method, properties, body):
        body = json.loads(body.decode())
        print(f"Пришло сообщение: {body}")
        r = es.index(index=index, body=body, id = body['id'])
        print(r)

    channel.queue_declare(queue="search",durable=True)
    channel.basic_consume(queue="search", on_message_callback=callback, auto_ack=True)

    print('Начинаем слушать очередь search')
    channel.start_consuming()

@app.route('/health', methods=['GET'])
def health():
    return json.dumps({"message": "ок"},ensure_ascii = False)

@app.route('/api/v1/search/<offset>/<limit>/<param>/<val>', methods=['GET'])
def get(offset, limit, param,val):
    resp = es.search(index=index, query={"match":{param:val}}, size = limit, from_ = offset)
    print("Got {} hits:".format(resp["hits"]["total"]["value"]))
    j = json.dumps(resp["hits"]["hits"], cls=ListOfListsEncoder,ensure_ascii = False)
         
    return Response(j, mimetype='application/json')


t = threading.Thread(target=listen)
t.daemon = True
t.start()

if __name__ == '__main__':
    app.run(host="0.0.0.0")