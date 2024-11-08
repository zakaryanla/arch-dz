import json
import psycopg2
import os
import pika
import threading
from flask import Flask, request
from psycopg2.extras import RealDictCursor
from keycloak import KeycloakAdmin, KeycloakOpenIDConnection
from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics

def keycloak_connection():
    return KeycloakOpenIDConnection(
        server_url=os.environ.get('KEYCLOAK_URL','http://arch-kk.homework/'),
        username=os.environ.get('KEYCLOAK_USER','crud'),
        password=os.environ.get('KEYCLOAK_PASS','sadsfASdcsdf'),
        realm_name=os.environ.get('KEYCLOAK_REALM','app'),
        client_id=os.environ.get('KEYCLOAK_CLIENT_ID','crud'),
        client_secret_key=os.environ.get('KEYCLOAK_CLIENT_SECRET','Y9BkXRzSKdKbVqaC07nBUgJpOJbVZu4t'),
        verify=True)

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

def url(req):
    return '%s' % (req.url_rule)

def userid():
    return request.headers.get('X-Auth-Request-User') 

def rmq():
    credentials = pika.PlainCredentials(os.environ.get('RMQ_LOGIN', ""), os.environ.get('RMQ_PASS', ""))
    parameters = pika.ConnectionParameters(os.environ.get('RMQ_HOSTNAME', "localhost"),
                                        5672,
                                        '/',
                                        credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    def callback(ch, method, properties, body):
        body = json.loads(body.decode())
        print(f"Пришло сообщение: {body}")
        keycloak_admin = KeycloakAdmin(connection=keycloak_connection())
        userKK = keycloak_admin.get_user(body['guid'])
        print(f"Ответ КК : {userKK}")

        if body['status'] == 'OK' and body['message'] == 'Операция прошла успешно':
            message = f"Уважаемый {userKK['lastName']}  {userKK['firstName']}, покупка {body['product']} прошла успешно. Текущий баланс: {body['current_value']} р."
        elif body['status'] == 'NOOK' and body['message'] == 'Недостаточно средств на кошельке':
            message = f"Уважаемый {userKK['lastName']}  {userKK['firstName']}, покупка {body['product']} прошла неуспешно. Недостаточно средств. Текущий баланс: {body['current_value']}р., стоимость товара: {0-body['change_value']}р."

        print(message)
        query_insert_history = f"insert into notifications.history(userid, text) values ('{body['guid']}', '{message}')"
        execute(query_insert_history, True)

    channel.basic_consume(queue='orders', on_message_callback=callback, auto_ack=True)

    print('Начинаем слушать очередь')
    channel.start_consuming()

t = threading.Thread(target=rmq)
t.daemon = True
t.start()
app = Flask(__name__)

metrics = GunicornPrometheusMetrics(app, group_by=url)

def execute(query, comm: bool):
    conn = psycopg2.connect('')
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(query)
    if comm:
        conn.commit() 
    else:
        result = cursor.fetchall()
        cursor.close()
        return result
    conn.close()

def userid():
    return request.headers.get('X-Auth-Request-User') 

@app.route('/api/v1/notifications/list', methods=['GET'])
def list():
    if not userid():
       return json.dumps({"message": "Отсутствует авторизация"},ensure_ascii = False)
    
    query_select_history = f"select id,     userid, text,status,to_char(created,'yyyy-mm-dd hh24:mi') as created from notifications.history where userid = '{userid()}'"
    res = execute(query_select_history, False)
    print(res)
    return json.dumps(res,ensure_ascii = False)

if __name__ == '__main__':
    app.run(host="0.0.0.0")
    
