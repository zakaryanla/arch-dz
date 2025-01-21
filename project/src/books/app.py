import json
import psycopg2
import os
import pika
import uuid
import requests
import datetime
from flask import Flask,Response, request, send_file
from psycopg2.extras import RealDictCursor
from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics
from minio import Minio
from minio.commonconfig import Tags

def url(req):
    return '%s' % (req.url_rule)

app = Flask(__name__)
metrics = GunicornPrometheusMetrics(app, group_by=url)


def userid():
    return request.headers.get('X-Auth-Request-User') 

def groups():
    return request.headers.get('X-Auth-Request-Groups') 

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

client = Minio(os.environ.get('MINIO_URL', "arch-minio-api.homework"),
    access_key=os.environ.get('MINIO_ACCESS', "SfuETSxNG3ATCL9Vo5lZ"),
    secret_key=os.environ.get('MINIO_SECRET', "GWah2A7g9IlL42KuYmg00cP9sYFJrsYYHvA7eaQA"),
    secure=False,
    cert_check=False
)

bucket = 'lib'

# {"price": "100", "lvl": "Extra", "summary": "Война и мир", "description": "Книга о войне и мире", "tags": "Книга, Толстой, Роман", "author": "Толстой"}
@app.route('/api/v1/book/full', methods=['PUT'])
def putf():
    if not userid():
       return json.dumps({"message": "Отсутствует авторизация"},ensure_ascii = False)
    elif "role:admins" not in groups():
        return json.dumps({"message": "Отсутствуют права"},ensure_ascii = False)
    file = request.files['book']
    meta = request.form.get('meta')
    meta = json.loads(meta)
    r = {}

    print(meta)

    query_check = f"select id from books.books where summary = '{meta['summary']}' and author = '{meta['author']}'"
    query_check_res = execute(query_check, False)

    if not query_check_res:
        u = str(uuid.uuid4())
        r['messsage'] = "Книга успешно добавлена"
    else:
        u = query_check_res['id']
        r['messsage'] = "Данные успешно обновлены"

    r['id'] = u
    # грузим в s3
    # tags = Tags(for_object=True)
    # tags["user"] = str(u)
    result = client.put_object(
        bucket, str(u), file, length=-1, part_size=10*1024*1024, content_type="application/pdf"
        # tags=tags,
        # metadata={"My-Project": "one"},
    )
    print(
        "created {0} object; etag: {1}, version-id: {2}".format(
            result.object_name, result.etag, result.version_id,
        ),
    )

    # добавляем в БД
    meta['id'] = u
    query_insert_history = f"""insert into books.books(id, price, lvl, summary,author) values ('{meta['id']}', {meta['price']}, '{meta['lvl']}', '{meta['summary']}', '{meta['author']}' ) 
    ON CONFLICT (id) DO UPDATE
    SET price = {meta['price']}, lvl = '{meta['lvl']}';
    """
    execute(query_insert_history, True)

    # отправляем в MQ
    print("отправляем в MQ: " + str(meta) )
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.basic_publish(exchange='book',
                    routing_key='full',
                    properties=properties,
                    body=json.dumps(meta,ensure_ascii = False))
    connection.close()
    print("Отправлено сообщение в MQ")

    return Response(json.dumps(r,ensure_ascii = False), mimetype='application/json')

# {"price": "100", "lvl": "Extra", "summary": "Война и мир", "description": "Книга о войне и мире", "tags": "Книга, Толстой, Роман", "author": "Толстой"}
@app.route('/api/v1/book/preview', methods=['PUT'])
def putp():
    if not userid():
       return json.dumps({"message": "Отсутствует авторизация"},ensure_ascii = False)
    elif "role:admins" not in groups():
        return json.dumps({"message": "Отсутствуют права"},ensure_ascii = False)
    print("Доступ предоставлен")
    meta = request.get_json(force=True)
    query_check = f"select id from books.books where summary = '{meta['summary']}' and author = '{meta['author']}'"
    query_check_res = execute(query_check, False)
    r = {}

    if not query_check_res:
        u = str(uuid.uuid4())
        r['messsage'] = "Книга успешно добавлена"
    else:
        u = query_check_res['id']
        r['messsage'] = "Данные успешно обновлены"
    r['id'] = u
    # добавляем в БД
    meta['id'] = u
    query_insert_history = f"""insert into books.books(id, price, lvl, summary,author) values ('{meta['id']}', {meta['price']}, '{meta['lvl']}', '{meta['summary']}', '{meta['author']}' ) 
    ON CONFLICT (id) DO UPDATE
    SET price = {meta['price']}, lvl = '{meta['lvl']}';
    """
    execute(query_insert_history, True)

    # отправляем в MQ
    print("отправляем в MQ: " + str(meta) )
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.basic_publish(exchange='book',
                    routing_key='preview',
                    properties=properties,
                    body=json.dumps(meta,ensure_ascii = False))
    connection.close()
    print("Отправлено сообщение в MQ")

    return Response(json.dumps(r,ensure_ascii = False), mimetype='application/json')

@app.route('/health', methods=['GET'])
def health():
    execute("select 1", False)
    return json.dumps({"message": "ок"},ensure_ascii = False)

# {"id": "67b04a0e-98da-40bc-a52e-22fda6a3b32f"}
@app.route('/api/v1/book/<guid>', methods=['GET'])
def get(guid):
    if not userid():
       return json.dumps({"message": "Отсутствует авторизация"},ensure_ascii = False)
    print(str(datetime.datetime.now()) + " Пришел запрос")
    price = f"select lvl from books.books where id = '{guid}'"
    p = execute(price, False)
    print(str(datetime.datetime.now()) + " Проверили в БД: ")
    j = f"""{{ "book": "{guid}","subscription": "{p['lvl']}","userid": "{userid()}" }}"""
    print(str(datetime.datetime.now()) + " Вызов payment")
    url = os.environ.get('PAYMENT_URL', "http://127.0.0.1:3000/int/api/v1/payment/check")
    print(str(datetime.datetime.now()) + " Вызов payment2")

    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}

    perm = requests.post(url, data=j,headers=headers)
    print(str(datetime.datetime.now()) + " Ответ от payment" + perm.text)

    resp = (json.loads(perm.text))

    if resp['message']:
        response = None
        print(str(datetime.datetime.now()) + " Вызов S3")
        try:
            response = client.get_object(
                bucket, guid
            )
            print(str(datetime.datetime.now()) + " Ответ S3")
            return Response(response.data, mimetype='application/pdf')
            # return send_file(response.data, mimetype='application/pdf')
        finally:
            if response:
                response.close()
                response.release_conn()

    else:
        return Response('{"message": "Отсутствуют права на книгу"}', mimetype='application/json')

if __name__ == '__main__':
    app.run(host="0.0.0.0")