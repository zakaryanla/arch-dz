import json
import psycopg2
import os
import pika
import threading
from flask import Flask, request
from psycopg2.extras import RealDictCursor
from keycloak import KeycloakAdmin, KeycloakOpenIDConnection
from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def keycloak_connection():
    return KeycloakOpenIDConnection(
        server_url=os.environ.get('KEYCLOAK_URL','http://arch-kk.homework/'),
        username=os.environ.get('KEYCLOAK_USER','adminlib'),
        password=os.environ.get('KEYCLOAK_PASS','sadsfASdcsdf'),
        realm_name=os.environ.get('KEYCLOAK_REALM','app'),
        client_id=os.environ.get('KEYCLOAK_CLIENT_ID','Adminlib'),
        client_secret_key=os.environ.get('KEYCLOAK_CLIENT_SECRET','wZqn7HCVUy1RH8lgMywqddVPBBjV0XkT'),
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
    credentials = pika.PlainCredentials(os.environ.get('RMQ_LOGIN', "guest"), os.environ.get('RMQ_PASS', "guest"))
    parameters = pika.ConnectionParameters(os.environ.get('RMQ_HOSTNAME', "localhost"),
                                        5672,
                                        '/',    
                                        credentials)
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    def callback(ch, method, properties, body):
        body = json.loads(body.decode())
        print(f"Пришло сообщение: {body}")
        query_select_sub = f"select distinct userid from nf.sub where bookid = '{body['id']}'"
        users_list = execute(query_select_sub, False)
        print(users_list)
        for i in users_list:
            keycloak_admin = KeycloakAdmin(connection=keycloak_connection())
            userKK = keycloak_admin.get_user(i['userid'])
            print(f"Ответ КК : {userKK}")

            port = os.environ.get('SMTP_PORT','465')
            smtp_server = os.environ.get('SMTP_SERVER','')
            sender_email = os.environ.get('SMTP_SENDER','')
            receiver_email = userKK['email']
            password = os.environ.get('SMTP_PASS','')

            message = MIMEMultipart("alternative")
            message["Subject"] = "Нужная книга появилась в доступе!"
            message["From"] = sender_email
            message["To"] = receiver_email
            # Create the plain-text and HTML version of your message
            text = f"""
            Уважаемый {userKK['firstName']} {userKK['lastName']},
            Книга {body['summary']} автора {body['author']} стала доступна для чтения!
            """
            part1 = MIMEText(text, "plain")
            message.attach(part1)

            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, receiver_email, message.as_string())
                server.quit()
                print("Готово!")

    channel.queue_declare(queue="subscriptions",durable=True)
    channel.basic_consume(queue='subscriptions', on_message_callback=callback, auto_ack=True)

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

@app.route('/health', methods=['GET'])
def health():
    execute("select 1", False)
    return json.dumps({"message": "ок"},ensure_ascii = False)

@app.route('/api/v1/subscriptions/subscription', methods=['GET'])
def list():
    if not userid():
       return json.dumps({"message": "Отсутствует авторизация"},ensure_ascii = False)
    
    query_select_history = f"select id, userid, text,status,to_char(created,'yyyy-mm-dd hh24:mi') as created from nf.history where userid = '{userid()}'"
    res = execute(query_select_history, False)
    print(res)
    return json.dumps(res,ensure_ascii = False)

# {"bookid": ""}
@app.route('/api/v1/subscriptions/subscription', methods=['POST'])
def subcreate():
    if not userid():
       return json.dumps({"message": "Отсутствует авторизация"},ensure_ascii = False)
    body = request.get_json(force=True)
    query_insert_sub = f"insert into nf.sub(userid, bookid) values ('{userid()}', '{body['bookid']}')"
    execute(query_insert_sub, True)
    res = {}
    res['status'] = "Подписка создана"
    return json.dumps(res,ensure_ascii = False)

@app.route('/api/v1/subscriptions/subscription', methods=['DELETE'])
def subdel():
    if not userid():
       return json.dumps({"message": "Отсутствует авторизация"},ensure_ascii = False)
    body = request.get_json(force=True)
    query_insert_sub = f"delete from nf.sub where userid = '{userid()}' and bookid = '{body['bookid']}'"
    execute(query_insert_sub, True)
    res = {}
    res['status'] = "Подписка удалена"
    return json.dumps(res,ensure_ascii = False)

if __name__ == '__main__':
    app.run(host="0.0.0.0")
    
