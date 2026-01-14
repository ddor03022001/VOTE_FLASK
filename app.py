from flask import Flask, render_template, g, request, redirect, url_for, session, jsonify
from flask_cors import CORS
from psycopg2.pool import ThreadedConnectionPool
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration from environment variables
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_NAME = os.getenv('DB_NAME', 'odoopilot-22102024')
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASS = os.getenv('DB_PASS', '1234')
SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-in-production')

app.config['SECRET_KEY'] = SECRET_KEY

# Connection pool: min=5, max=20 connections
db_pool = ThreadedConnectionPool(5, 20, host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS)

# Connect PostgreSQL
def get_db_connection():
    return db_pool.getconn()

@app.before_request
def connect_to_db():
    if not hasattr(g, 'db_connection'):
        g.db_connection = get_db_connection()

@app.after_request
def close_db_connection(response):
    if hasattr(g, 'db_connection'):
        db_pool.putconn(g.db_connection)
    return response

# Get vote status
def get_is_open_from_db():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT is_open FROM status_vote_festival WHERE id = 1')
        is_open = cursor.fetchone()[0]
        cursor.close()
        return is_open
    finally:
        db_pool.putconn(conn)

# ============================================
# API ENDPOINTS
# ============================================

# API: Get ranking data
@app.route('/api/ranking', methods=['GET'])
def api_ranking():
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, vote_number, numerical 
            FROM vote_festival_model 
            ORDER BY vote_number DESC, numerical ASC
        """)
        teams = cursor.fetchall()
        cursor.close()
        
        result = []
        for idx, team in enumerate(teams):
            result.append({
                'id': team[0],
                'name': team[1],
                'votes': team[2],
                'rank': idx + 1
            })
        
        return jsonify({'teams': result, 'is_open': get_is_open_from_db()})
    finally:
        db_pool.putconn(conn)

# API: Start voting (Admin)
@app.route('/api/start_vote', methods=['POST'])
def api_start_vote():
    if 'user_id' not in session or session.get('user_code') != 'ADMIN':
        return jsonify({"error": "Unauthorized"}), 401
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE status_vote_festival SET is_open = 2 WHERE id = 1')
        conn.commit()
        cursor.close()
        return jsonify({"status": "success", "is_open": 2})
    finally:
        db_pool.putconn(conn)

# API: End voting (Admin)
@app.route('/api/end_vote', methods=['POST'])
def api_end_vote():
    if 'user_id' not in session or session.get('user_code') != 'ADMIN':
        return jsonify({"error": "Unauthorized"}), 401
    
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('UPDATE status_vote_festival SET is_open = 1 WHERE id = 1')
        conn.commit()
        cursor.close()
        return jsonify({"status": "success", "is_open": 1})
    finally:
        db_pool.putconn(conn)

# API: Get vote status
@app.route('/api/status', methods=['GET'])
def api_status():
    return jsonify({"is_open": get_is_open_from_db()})

# ============================================
# ADMIN ROUTES
# ============================================

# Admin: Leaderboard page
@app.route('/admin/leaderboard')
def admin_leaderboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session.get('user_code') != 'ADMIN':
        return redirect(url_for('index'))
    
    is_open = get_is_open_from_db()
    return render_template('leaderboard.html', is_open=is_open)

# ============================================
# USER ROUTES
# ============================================

# Update user confirm festival
@app.route('/get_user_confirm', methods=['POST'])
def get_user_confirm():
    userId = request.json.get('user_id')
    if not userId:
        return jsonify({"error": "Invalid request"}), 400

    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE res_user_vote_festival SET has_vote = True WHERE id = %s", (userId,))
        conn.commit()
        cursor.close()
    finally:
        db_pool.putconn(conn)

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

        conn = None
        try:
            conn = db_pool.getconn()
            cur = conn.cursor()
            login = login.replace(' ', '') 
            cur.execute("SELECT id, name, code, phone_number, position, company_name, has_vote, room_number, car_number FROM res_user_vote_festival WHERE REPLACE(phone_number, ' ', '') = %s", (login,))
            user = cur.fetchone()
            cur.close()

            if user:
                return render_template('detail_checkin.html', user=user)
            else:
                error = "Đăng nhập thất bại! Số điện thoại không đúng."
                return render_template('checkin.html', error=error)
        finally:
            if conn:
                db_pool.putconn(conn)

    return render_template('checkin.html', error=error)

# Route login
@app.route('/', methods=['GET', 'POST'])
def login():
    error = None 
    if request.method == 'POST':
        login = request.form.get('login')
        
        if not login:
            error = "Vui lòng nhập đầy đủ số điện thoại!"
            return render_template('login.html', error=error)

        login = login.replace(' ', '')
        conn = None
        try:
            conn = db_pool.getconn()
            cur = conn.cursor()
            cur.execute("""
                SELECT id, name, code, phone_number, position, company_name, has_vote 
                FROM res_user_vote_festival 
                WHERE REPLACE(phone_number, ' ', '') = %s
            """, (login,))
            user = cur.fetchone()
            cur.close()
            
            if user:
                session['user_id'] = user[0]
                session['user_login'] = user[1]
                session['user_code'] = user[2]
                # Redirect admin to leaderboard
                if user[2] == 'ADMIN':
                    return redirect(url_for('admin_leaderboard'))
                return redirect(url_for('index'))
            else:
                error = "Đăng nhập thất bại! Số điện thoại không đúng."
        finally:
            if conn:
                db_pool.putconn(conn)

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

    conn = None
    try:
        conn = db_pool.getconn()
        cur = conn.cursor()

        # Lấy danh sách lễ hội
        cur.execute("""
            SELECT id, name, vote_number, numerical 
            FROM vote_festival_model
            ORDER BY numerical ASC
        """)
        festivals = cur.fetchall()

        # Lấy danh sách các mục đã bầu của user
        user_id = session['user_id']
        cur.execute("""
            SELECT vote_festival_model_id 
            FROM vote_festival_model_line 
            WHERE user_id = %s
        """, (user_id,))
        user_votes = {row[0]: True for row in cur.fetchall()}

        cur.close()

        is_open = get_is_open_from_db()
    finally:
        if conn:
            db_pool.putconn(conn)

    return render_template('index.html', festivals=festivals, user_votes=user_votes, is_open=is_open)

@app.route('/vote', methods=['POST'])
def vote():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    # Check if voting is open
    if get_is_open_from_db() != 2:
        return jsonify({"error": "Voting is closed", "action": "closed"}), 400

    vote_id = request.json.get('vote_id')
    if not vote_id:
        return jsonify({"error": "Invalid request"}), 400

    conn = g.db_connection
    cur = conn.cursor()

    user_id = session['user_id']
    cur.execute("SELECT * FROM vote_festival_model_line WHERE user_id = %s AND vote_festival_model_id = %s", (user_id, vote_id))
    existing_vote = cur.fetchone()
    cur.execute("SELECT * FROM vote_festival_model_line WHERE user_id = %s", (user_id,))
    number_vote = cur.fetchall()

    if existing_vote:
        cur.execute("DELETE FROM vote_festival_model_line WHERE user_id = %s AND vote_festival_model_id = %s", (user_id, vote_id))
        cur.execute("UPDATE vote_festival_model SET vote_number = vote_number - 1 WHERE id = %s", (vote_id,))
        action = 'removed'
    else:
        if len(number_vote) >= 1:
            action = 'warning'
        else:
            cur.execute("INSERT INTO vote_festival_model_line (user_id, vote_festival_model_id) VALUES (%s, %s)", (user_id, vote_id))
            cur.execute("UPDATE vote_festival_model SET vote_number = vote_number + 1 WHERE id = %s", (vote_id,))
            action = 'added'

    cur.execute("SELECT vote_number FROM vote_festival_model WHERE id = %s", (vote_id,))
    updated_vote_number = cur.fetchone()[0]
    conn.commit() 

    cur.close()

    return jsonify({"vote_number": updated_vote_number, "action": action})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
