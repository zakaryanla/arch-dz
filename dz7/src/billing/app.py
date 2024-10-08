import json
import psycopg2
import os
from flask import Flask,Response, request, jsonify
from psycopg2.extras import RealDictCursor
from keycloak import KeycloakAdmin
from keycloak import KeycloakOpenIDConnection
from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics
from flask_swagger import swagger


def keycloak_connection():
    return KeycloakOpenIDConnection(
        server_url=os.environ.get('KEYCLOAK_URL','http://arch-kk.homework/'),
        username=os.environ.get('KEYCLOAK_USER','crud'),
        password=os.environ.get('KEYCLOAK_PASS','sadsfASdcsdf'),
        realm_name=os.environ.get('KEYCLOAK_REALM','app'),
        client_id=os.environ.get('KEYCLOAK_CLIENT_ID','crud'),
        client_secret_key=os.environ.get('KEYCLOAK_CLIENT_SECRET','Y9BkXRzSKdKbVqaC07nBUgJpOJbVZu4t'),
        verify=True)

def url(req):
    return '%s' % (req.url_rule)

app = Flask(__name__)
# metrics = GunicornPrometheusMetrics(app, group_by=url)

def check_header():
    print("Проверяем авторизацию")
    if not userid():
        print("Авторизации нет")
        return False
    print(f"Авторизация есть: {userid()}")
    return True

def check_user(column, username):
    query_select = f"""SELECT * FROM billing.users where {column} = '{username}' """
    return execute(query_select, False)

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

def userid():
    return request.headers.get('X-Auth-Request-User') 

def checAccessDenied():
    try:
        if not check_header():
            return True
        
        user = check_user("id", userid())
        if not user:
            print(f"Пользователя {userid()} нет, создаем")
            keycloak_admin = KeycloakAdmin(connection=keycloak_connection())
            userKK = keycloak_admin.get_user(userid())

            create_user({
                "id": userKK['id'],
                "username": userKK['username'],
                "firstName": userKK['firstName'],
                "lastName": userKK['lastName'],
                "email": userKK['email'],
                "phone": userKK['attributes']['phone'][0]
            })
    except Exception as e:
        print(e)
        return True

def create_user(data):    
    query_insert = f""" insert into billing.users(id) values ('{data['id']}') """
    execute(query_insert, True)

@app.route("/spec")
def spec():
    swag = swagger(app)
    swag['info']['version'] = "1.0"
    swag['info']['title'] = "My API"
    return jsonify(swag)

@app.route('/api/v1/billing/check', methods=['GET'])
def getId():
    if checAccessDenied():
        print("Права нет у " + userid())
        return json.dumps({"message": "Отсутствуют права"},ensure_ascii = False)
    
    userInfo = check_user("id", userid())['bill']
    message = f"""{{"sum": {userInfo} }} """
    return Response(message, mimetype='application/json')

@app.route('/api/v1/billing/change', methods=['PATCH'])
def money():
    data = request.get_json(force=True)
    print(f"Изменение суммы кошелька: {data['sum']}")

    print("Проверяем права у " + userid())
    if checAccessDenied():
        print("Права нет у " + userid())
        return json.dumps({"status": "NOOK", "message": "Отсутствуют права"},ensure_ascii = False)
    print("Права есть у" + userid())

    query_check = f"select bill+{data['sum']} as resault from billing.users where id = '{userid()}'"
    check_resault = execute(query_check, False)
    
    if check_resault['resault'] < 0:
        current_value = (0-data['sum']) + check_resault['resault']
        print(f"Недостаточно средств. Старое значение: {current_value}, Новое значение: {check_resault['resault']} ")
        message = f"""{{"status": "NOOK", "message": "Недостаточно средств на кошельке", "guid": "{userid()}", "current_value": {current_value}, "change_value": {data['sum']}}}"""
        return Response(message, mimetype='application/json')
    
    print(f"Новое значение кошелька: {check_resault['resault']}")
    query_update = f"update billing.users set bill=bill+{data['sum']}  where id = '{userid()}'"
    execute(query_update, True)

    query_insert_history = f"insert into billing.history(userid, sum) values ('{userid()}', {data['sum']}) "
    execute(query_insert_history, True)

    message= f"""{{"status": "OK", "message": "Операция прошла успешно", "guid": "{userid()}", "change_value": {data['sum']}, "current_value": {check_resault['resault']}}}"""
    return Response(message, mimetype='application/json')


if __name__ == '__main__':
    app.run(host="0.0.0.0")