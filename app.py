from flask import Flask, request, jsonify, make_response, render_template, session, current_app
import jwt
import uuid
from datetime import datetime, timedelta
from functools import wraps
from decouple import config
from db import conn

app = Flask(__name__)
app.config['SECRET_KEY'] = config('SECRET_KEY')

def token_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'Alert!': 'Token is missing!'})
        try:
            token = token.split(" ")[1]
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            request.current_user = payload
        except jwt.InvalidTokenError:
            return jsonify({'Alert!': 'Invalid Token!'})
        return func(*args, **kwargs)
    return decorated

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if data['username'] == 'admin1' and data['password'] == '1234567':
        session['logged_in'] = True
        token = jwt.encode({
            'user': data['username'],
            'exp': datetime.utcnow() + timedelta(seconds=400)
        },
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        return {'token': token}
    return make_response('Unable to verify', 403, {'WWW-Authenticate': 'Basic realm:"Authentication Failed!'})

@app.route('/items', methods=['GET'])
@token_required
def get_items():
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items;")
        result = cursor.fetchall()
        item_list = []
        for row in result:
            item_list.append({
                'id': row[0],
                'name': row[1],
                'price': row[2]
            })
        cursor.close()
        return jsonify({"items": item_list})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/item', methods=['GET'])
@token_required
def get_item():
    id = request.args.get('id')
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM items WHERE id = %s;", (id,))
        result = cursor.fetchone()
        cursor.close()
        if result:
            return jsonify({
                'id': result[0],
                'name': result[1],
                'price': result[2]
            })
        else:
            return jsonify({'message': "Record doesn't exist"}), 404
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/items', methods=['POST'])
@token_required
def add_item():
    request_data = request.get_json()
    if "name" not in request_data or "price" not in request_data:
        return jsonify({"message": "'name' and 'price' must be included in the body!"}), 404
    item_id = str(uuid.uuid4().hex)
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO items (id, name, price) VALUES (%s, %s, %s);", (item_id, request_data['name'], request_data['price']))
        conn.commit()
        cursor.close()
        return jsonify({"message": "Item added successfully!", "item_id": item_id})
    except Exception as e:
        return jsonify({'error': str(e)})

# ...

@app.route('/item', methods=['PUT'])
@token_required
def update_item():
    id = request.args.get('id')
    if id is None:
        return {"message": "Given Id not found!"}, 404

    request_data = request.get_json()
    if "name" not in request_data or "price" not in request_data:
        return {"message": "'name' and 'price' must be included in the body!"}, 404

    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE items SET name = %s, price = %s WHERE id = %s;", (request_data['name'], request_data['price'], id))
        conn.commit()
        cursor.close()

        if cursor.rowcount > 0:
            return {"message": "Item Updated Successfully!"}, 200
        else:
            return {"message": "Item not found"}, 404

    except Exception as e:
        return {"error": str(e)}


@app.route('/item', methods=['DELETE'])
@token_required
def delete_item():
    id = request.args.get('id')
    if id is None:
        return {"message": "Given Id not found!"}, 404

    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM items WHERE id = %s;", (id,))
        conn.commit()
        cursor.close()

        if cursor.rowcount > 0:
            return {"message": "Item deleted Successfully"}
        else:
            return {"message": "Item not found"}, 404

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    app.run(debug=True)
