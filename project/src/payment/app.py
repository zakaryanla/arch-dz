import json
import psycopg2
import uuid
import datetime
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
        result = cursor.fetchall()
        cursor.close()
        return result
    conn.close()

def buy(body):
    r = {}
    print(body)

    if body['sum']<0: 
        cnt = f"""select COALESCE(sum(sum),0) as sum from payment.users_balance where userid = '{body['userid']}' """
        available = execute(cnt,False)
        print(f"Денег на счету: {available}")
        
        if 0-body['sum'] > available[0]['sum']:
            r['message'] = "Недостаточно средств"
        else:
            new = f"""insert into payment.users_balance(tr_guid, userid, sum) values ('{body['guid']}', '{body['userid']}', {body['sum']})"""
            execute(new, True)
            r['message'] = "Успешно"
    elif body['sum']>0: 
            new = f"""insert into payment.users_balance(tr_guid, userid, sum) values ('{body['guid']}', '{body['userid']}', {body['sum']})"""
            execute(new, True)
            r['message'] = "Успешно"
    return r

@app.route('/health', methods=['GET'])
def health():
    execute("select 1", False)
    return json.dumps({"message": "ок"},ensure_ascii = False)

@app.route('/api/v1/payment/balance', methods=['GET'])
def getSt():
    cnt = f"""select COALESCE(sum(sum),0) as sum from payment.users_balance where userid = '{userid()}' """
    available = execute(cnt,False)
    print(f"Денег на счету: {available[0]['sum']}")
    r = {}
    r['sum'] = available[0]['sum']
    return Response(json.dumps(r,ensure_ascii = False), mimetype='application/json')

# {"guid": "6c6af38e-1e76-4b8a-9284-efd9a0842f0d", sum": -100}
@app.route('/api/v1/payment/balance', methods=['POST'])
def balance():
    body = request.get_json(force=True)
    body['userid'] = userid() 
    return Response(json.dumps(buy(body),ensure_ascii = False), mimetype='application/json')

# { "subscription": "Extra", "duration": 2}
@app.route('/api/v1/payment/subscription', methods=['POST'])
def subscription():
    body = request.get_json(force=True)
    r = {}

    check_exists = f"select 1 from payment.users_subscription u where u.userid = '{userid()}' and u.date_before > now()"
    current = execute(check_exists, False)
    if current:
        r['message'] = "Подписка уже существует, дожидтесь окончания"
    else:
        msg = {}
        msg['guid'] = str(uuid.uuid4())
        msg['userid'] = userid() 
        price = f"select sum from payment.subscriptions where subscription = '{body['subscription']}'"
        p = execute(price, False)
        msg['sum'] = 0-(p[0]['sum'] * body['duration'])
        
        check_money = buy(msg)
        if check_money['message'] == 'Успешно':
            add = f"insert into payment.users_subscription values ('{userid()}', '{body['subscription']}', current_date +  interval '{body['duration']} month', now())"
            execute(add, True)
            r['message'] = "Подписка создана"
        else:
            r['message'] = "Недостаточно средств"
    return Response(json.dumps(r,ensure_ascii = False), mimetype='application/json')

# { "book": "07f0f7ee-4c58-4bec-bfbf-5184c7adb8ff","sum": -10}
@app.route('/api/v1/payment/book', methods=['POST'])
def book():
    body = request.get_json(force=True)
    r = {}

    check_exists = f"select 1 from payment.users_books u where u.userid = '{userid()}' and u.bookid = '{body['book']}'"
    current = execute(check_exists, False)
    print(current)
    if current:
        r['message'] = "Книга уже куплена"
    else:
        msg = {}
        msg['guid'] = str(uuid.uuid4())
        msg['userid'] = userid() 
        msg['sum'] = body['sum']
        
        check_money = buy(msg)
        if check_money['message'] == 'Успешно':
            add = f"insert into payment.users_books values ('{userid()}', '{body['book']}', now())"
            execute(add, True)
            r['message'] = "Книга успешно куплена"
        else:
            r['message'] = "Недостаточно средств"
    return Response(json.dumps(r,ensure_ascii = False), mimetype='application/json')

# { "book": "07f0f7ee-4c58-4bec-bfbf-5184c7adb8ff","subscription": "Extra","userid": "1c6af38e-1e76-4b8a-9284-efd9a0842f0d" }
@app.route('/api/v1/payment/check', methods=['POST'])
def check():
    body = request.get_json(force=True)
    print(str(datetime.datetime.now()) + " Пришел запрос:" + str(body))
    r = {}

    check_sub = f"select 1 from payment.users_subscription u, payment.subscriptions s where u.userid = '{body['userid']}' and u.date_before > now() and s.subscription = u.subscription and (select lvl from payment.subscriptions where subscription = '{body['subscription']}') <= s.lvl"
    current_sub = execute(check_sub, False)
    print(str(datetime.datetime.now()) + " Первая проверка в БД на подписку")

    if current_sub:
        r['message'] = True
        print(str(datetime.datetime.now()) + " Подписка есть")
    else:
        print(str(datetime.datetime.now()) + " Подписки  нет, проверяем книгу")
        check_book = f"select 1 from payment.users_books where userid = '{body['userid']}' and bookid = '{body['book']}'"
        current_book = execute(check_book, False)
        print(str(datetime.datetime.now()) + " Покупка книги проверена")
        if current_book:
            r['message'] = True
        else:
            r['message'] = False

    print(str(datetime.datetime.now()) + " Ответ")
    return Response(json.dumps(r,ensure_ascii = False), mimetype='application/json')


if __name__ == '__main__':
    app.run(host="0.0.0.0")