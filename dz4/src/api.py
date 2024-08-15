import json
import psycopg2
import os
from flask import Flask,Response, request
from psycopg2.extras import RealDictCursor


app = Flask(__name__)

DATABASE_CONFIG = { 
    "database": os.environ.get("DB_DATABASE"), 
    "user": os.environ.get("DB_USER"), 
    "password": os.environ.get("DB_PASS"), 
    "host": os.environ.get("DB_URL"), 
    "port":  os.environ.get("DB_PORT"), 
} 

def check_user(column, username):
    query_select = f"""SELECT * FROM users where {column} = '{username}' """
    return execute(query_select, False)

def execute(query, comm: bool):
    conn = psycopg2.connect(database=DATABASE_CONFIG.get('database'), 
        user=DATABASE_CONFIG.get('user'), 
        password=DATABASE_CONFIG.get('password'), 
        host=DATABASE_CONFIG.get('host'), 
        port=DATABASE_CONFIG.get('port'))
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute(query)
    if comm:
        conn.commit() 
    else:
        result = cursor.fetchone()
        cursor.close()
        return result
    conn.close()
    

@app.route('/api/v1/user/<int:user_id>', methods=['GET'])
def get_user_id(user_id):
    user = check_user("id", user_id)
    if user:
        return  json.dumps(user,ensure_ascii = False)
    else:
        return json.dumps({"message": "Пользователь не найден"},ensure_ascii = False)
    
@app.route('/api/v1/user', methods=['POST'])
def add_user():
    data = request.get_json(force=True)

    if 'username' not in data:
        return json.dumps({"message": "Не передан логин"},ensure_ascii = False)
    
    id = check_user("username", data['username'])
    if id:
        return json.dumps({"message": "Пользователь существует"},ensure_ascii = False)
    
    query_insert = f""" insert into users(username, firstName, lastName, email, phone) values ('{data['username']}','{data['firstName']}','{data['lastName']}','{data['email']}','{data['phone']}') """
    execute(query_insert, True)
    user = check_user("username", data['username'])
    return json.dumps(user,ensure_ascii = False)

@app.route('/api/v1/user/<int:user_id>', methods=['DELETE'])
def del_user(user_id):
    id = check_user("id", user_id)
    if not id:
        return json.dumps({"message": "Пользователь не  существует"},ensure_ascii = False)
    
    query_delete = f""" DELETE FROM users where id = {user_id} """
    execute(query_delete, True)
    return json.dumps({"message": "Пользователь удален"},ensure_ascii = False)

@app.route('/api/v1/user/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json(force=True)

    id = check_user("id", user_id)
    if not id:
        return json.dumps({"message": "Пользователь не  существует"},ensure_ascii = False)
    
    column = ["firstName","lastName","email","phone"]
    set = ""
    n = 1
    m = 0

    for i in data:
        if i in column:
            m+=1

    for i in data:
        if i in column:
            if n == m:
                set += f""" {i} = '{data[i]}' """
            else:
                set += f""" {i} = '{data[i]}', """
            n+=1
    
    query_update = f"update users set {set} where id = {user_id}"
    execute(query_update, True)
    return json.dumps({"message": "Данные пользователя обновлены "},ensure_ascii = False)

if __name__ == '__main__':
    app.run(host="0.0.0.0")