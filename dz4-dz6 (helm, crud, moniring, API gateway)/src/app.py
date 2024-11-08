import json
import psycopg2
import os
from flask import Flask,Response, request, redirect, url_for
from psycopg2.extras import RealDictCursor
from keycloak import KeycloakAdmin
from keycloak import KeycloakOpenIDConnection
from prometheus_flask_exporter.multiprocess import GunicornPrometheusMetrics

def keycloak_connection():
    return KeycloakOpenIDConnection(
        server_url=os.environ.get('KEYCLOAK_URL'),
        username=os.environ.get('KEYCLOAK_USER'),
        password=os.environ.get('KEYCLOAK_PASS'),
        realm_name=os.environ.get('KEYCLOAK_REALM'),
        client_id=os.environ.get('KEYCLOAK_CLIENT_ID'),
        client_secret_key=os.environ.get('KEYCLOAK_CLIENT_SECRET'),
        verify=True)

def url(req):
    return '%s' % (req.url_rule)

app = Flask(__name__)
metrics = GunicornPrometheusMetrics(app, group_by=url)

def check_user(column, username):
    query_select = f"""SELECT * FROM users where {column} = '{username}' """
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

def checAccessDenied(user_id):
    user = check_user("id", user_id)
    if not user or user['username'] != login():
        return True
        
def login():
    return request.headers.get('X-Auth-Request-Preferred-Username')

def accessDenied():
    return json.dumps({"message": "Отсутствуют права"},ensure_ascii = False)

def create_user(data):
    id = check_user("username", data['username'])
    if id:
        return json.dumps({"message": "Пользователь существует"},ensure_ascii = False)
    
    query_insert = f""" insert into users(username, firstName, lastName, email, phone) values ('{data['username']}','{data['firstName']}','{data['lastName']}','{data['email']}','{data['phone']}') """
    execute(query_insert, True)
    user = check_user("username", data['username'])
    return json.dumps(user,ensure_ascii = False)

@app.route('/api/callback', methods=['GET'])
def oauth():
    user = request.headers.get('X-Auth-Request-User')
    uri = request.args.get('uri')
    checkExists = check_user("username", user)

    if not checkExists: 
        keycloak_admin = KeycloakAdmin(connection=keycloak_connection())
        userKK = keycloak_admin.get_user(user)

        create_user({
            "username": userKK['username'],
            "firstName": userKK['firstName'],
            "lastName": userKK['lastName'],
            "email": userKK['email'],
            "phone": userKK['attributes']['phone'][0]
        })

    return redirect(uri, code=302)

@app.route('/api/getId', methods=['GET'])
def getId():
    userInfo = check_user("username", login())
    
    return  json.dumps(userInfo,ensure_ascii = False)

@app.route('/api/v1/user/<int:user_id>', methods=['GET'])
def get_user_id(user_id):
    if checAccessDenied(user_id):
        return accessDenied()
    
    user = check_user("id", user_id)
    
    return  json.dumps(user,ensure_ascii = False)

@app.route('/api/v1/user/<int:user_id>', methods=['DELETE'])
def del_user(user_id):
    if checAccessDenied(user_id):
        return accessDenied()

    query_delete = f""" DELETE FROM users where id = {user_id} """
    execute(query_delete, True)
    return json.dumps({"message": "Пользователь удален"},ensure_ascii = False)

@app.route('/api/v1/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json(force=True)

    if checAccessDenied(user_id):
        return accessDenied()
    
    column = ["firstName","lastName","email","phone"]
    set = ""

    for i in data:
        if i in column:
            set += f""" {i} = '{data[i]}',"""
    set = set[:-1]

    query_update = f"update users set {set} where id = {user_id}"
    execute(query_update, True)
    return json.dumps({"message": "Данные пользователя обновлены "},ensure_ascii = False)
       
if __name__ == '__main__':
    app.run(host="0.0.0.0")