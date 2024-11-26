from flask import Flask, render_template, g, request, redirect, url_for, session, jsonify
from passlib.context import CryptContext
import psycopg2
from datetime import datetime, timedelta
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
socketio = SocketIO(app, async_mode='gevent')

# Setting PostgreSQL Odoo
DB_HOST = 'localhost'
DB_NAME = 'odoopilot-22102024' 
DB_USER = "admin"  
DB_PASS = "1234"  
SECRET_KEY = 'mysecretkey'  

app.config['SECRET_KEY'] = SECRET_KEY

# Connect PostgreSQL
def get_db_connection():
    conn = psycopg2.connect(
        host=DB_HOST,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )
    return conn

@app.before_request
def connect_to_db():
    if not hasattr(g, 'db_connection'):
        g.db_connection = get_db_connection()

@app.after_request
def close_db_connection(response):
    if hasattr(g, 'db_connection'):
        g.db_connection.close()
    return response

def get_is_open_from_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT is_open FROM status_vote_festival WHERE id = 1')
    is_open = cursor.fetchone()[0] 
    cursor.close()
    conn.close()
    return is_open

@app.route('/get_open_vote', methods=['POST'])
def get_open_vote():
    isOpen = request.json.get('is_open')
    if not isOpen:
        return jsonify({"error": "Invalid request"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    if isOpen == 1:
        cursor.execute('UPDATE status_vote_festival SET is_open = 2 WHERE id = 1')
        action = 'end'
    else:
        cursor.execute('UPDATE status_vote_festival SET is_open = 1 WHERE id = 1')
        action = 'start'
        
    conn.commit()
    cursor.close()
    conn.close()

    is_open = get_is_open_from_db()

    socketio.emit('open_vote', {
        'update_is_open': is_open,
        'action': action
    }, room=None)

    return jsonify({"is_open": is_open, "action": action})

@app.route('/get_user_confirm', methods=['POST'])
def get_user_confirm():
    userId = request.json.get('user_id')
    if not userId:
        return jsonify({"error": "Invalid request"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE res_user_vote_festival SET has_vote = True WHERE id = %s", (userId,))
        
    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"action": "success"})

# Route checkin
@app.route('/checkin', methods=['GET', 'POST'])
def Checkin():
    error = None
    if request.method == 'POST':
        login = request.form.get('checkin')
        
        if not login:
            error = "Vui lòng nhập đầy đủ số điện thoại!"
            return render_template('checkin.html', error=error)

        conn = g.db_connection
        cur = conn.cursor()
        
        cur.execute("SELECT id, name, code, phone_number, position, company_name, has_vote, room_number, car_number FROM res_user_vote_festival WHERE phone_number = %s", (login,))
        user = cur.fetchone()
        cur.close()

        if user:
            return render_template('detail_checkin.html', user=user)
        else:
            error = "Đăng nhập thất bại! Số điện thoại không đúng."
            return render_template('checkin.html', error=error)

    return render_template('checkin.html', error=error)

# Route login
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    session.pop('user_id', None) 
    session.pop('user_login', None) 
    session.pop('user_code', None)  
    if request.method == 'POST':
        login = request.form.get('login')
        
        if not login:
            error = "Vui lòng nhập đầy đủ số điện thoại!"
            return render_template('login.html', error=error)

        conn = g.db_connection
        cur = conn.cursor()
        
        cur.execute("SELECT id, name, code, phone_number, position, company_name, has_vote FROM res_user_vote_festival WHERE phone_number = %s", (login,))
        user = cur.fetchone()
        cur.close()

        if user and user[6]:
            session['user_code'] = user[2]
            session['user_id'] = user[0]
            session['user_login'] = user[1]
            return redirect(url_for('index')) 
        else:
            error = "Đăng nhập thất bại! Số điện thoại không đúng."
            return render_template('login.html', error=error)

    return render_template('login.html', error=error)

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None) 
    session.pop('user_login', None) 
    session.pop('user_code', None)   
    return redirect(url_for('login'))  

@app.route('/index')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))  

    conn = g.db_connection
    cur = conn.cursor()

    cur.execute("SELECT id, name, vote_number FROM vote_festival_model")
    festivals = cur.fetchall()

    user_id = session['user_id']
    user_votes = {}
    cur.execute("SELECT vote_festival_model_id FROM vote_festival_model_line WHERE user_id = %s", (user_id,))
    for row in cur.fetchall():
        user_votes[row[0]] = True

    cur.close()
    # if festivals:
    #     festivals_sorted = sorted(festivals, key=lambda x: x[2], reverse=True)
    # else:
    #     festivals_sorted = []
    is_open = get_is_open_from_db()

    return render_template('index.html', festivals=festivals, user_votes=user_votes, is_open=is_open)

@app.route('/vote', methods=['POST'])
def vote():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    vote_id = request.json.get('vote_id')
    if not vote_id:
        return jsonify({"error": "Invalid request"}), 400

    conn = g.db_connection
    cur = conn.cursor()

    user_id = session['user_id']
    cur.execute("SELECT * FROM vote_festival_model_line WHERE user_id = %s AND vote_festival_model_id = %s", (user_id, vote_id))
    existing_vote = cur.fetchone()

    if existing_vote:
        cur.execute("DELETE FROM vote_festival_model_line WHERE user_id = %s AND vote_festival_model_id = %s", (user_id, vote_id))
        cur.execute("UPDATE vote_festival_model SET vote_number = vote_number - 1 WHERE id = %s", (vote_id,))
        action = 'removed'
    else:
        cur.execute("INSERT INTO vote_festival_model_line (user_id, vote_festival_model_id) VALUES (%s, %s)", (user_id, vote_id))
        cur.execute("UPDATE vote_festival_model SET vote_number = vote_number + 1 WHERE id = %s", (vote_id,))
        action = 'added'

    cur.execute("SELECT vote_number FROM vote_festival_model WHERE id = %s", (vote_id,))
    updated_vote_number = cur.fetchone()[0]
    conn.commit() 

    cur.close()

    socketio.emit('update_vote', {
        'vote_festival_model_id': vote_id,
        'vote_number': updated_vote_number,
        'action': action
    }, room=None)

    return jsonify({"vote_number": updated_vote_number, "action": action})

@app.route('/get_likes', methods=['POST'])
def get_likes():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    vote_id = request.json.get('vote_id')
    if not vote_id:
        return jsonify({"error": "Invalid request"}), 400

    conn = g.db_connection
    cur = conn.cursor()

    cur.execute("SELECT user_id FROM vote_festival_model_line WHERE vote_festival_model_id = %s", (vote_id,))
    user_ids = cur.fetchall()

    list_user_votes = [user_id[0] for user_id in user_ids] 

    if list_user_votes:
        cur.execute("SELECT name FROM res_user_vote_festival WHERE id IN %s", (tuple(list_user_votes),))
        user_logins = cur.fetchall()
    else:
        user_logins = []
    cur.close()
        
    return jsonify({"status": "success", "likes": user_logins})

# Deadline vote
voting_deadline = datetime(2024, 11, 22, 14, 32, 00)

@app.route('/check_voting_status', methods=['GET'])
def check_voting_status():
    current_time = datetime.now()
    if current_time > voting_deadline:
        return jsonify({"status": "expired"})
    return jsonify({"status": "active"})

# Join room when user login success
@socketio.on('join_room')
def on_join(data):
    user_id = data['user_id']
    join_room(str(user_id))
    print(f"User {user_id} joined room.")

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
