from flask import Flask, render_template, g, request, redirect, url_for, session, jsonify
from passlib.context import CryptContext
import psycopg2
from flask_socketio import SocketIO, emit, join_room, leave_room

# Khởi tạo ứng dụng Flask và Flask-SocketIO
app = Flask(__name__)
socketio = SocketIO(app, async_mode='gevent')

# Cấu hình kết nối tới cơ sở dữ liệu Odoo
DB_HOST = 'localhost'
DB_NAME = 'odoopilot-22102024' 
DB_USER = "admin"  
DB_PASS = "1234"  
SECRET_KEY = 'mysecretkey'  

app.config['SECRET_KEY'] = SECRET_KEY

# Cấu hình mật khẩu
pwd_context = CryptContext(schemes=["pbkdf2_sha512"])

# Kết nối đến cơ sở dữ liệu PostgreSQL
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

# Route đăng nhập
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        
        if not login or not password:
            return "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu!", 400

        conn = g.db_connection
        cur = conn.cursor()
        
        # Kiểm tra tên đăng nhập và mật khẩu trong bảng res_users
        cur.execute("SELECT id, login, password FROM res_users WHERE login = %s", (login,))
        user = cur.fetchone()
        cur.close()

        if user and pwd_context.verify(password, user[2]):
            # Đăng nhập thành công, lưu thông tin vào session
            session['user_id'] = user[0]
            session['user_login'] = user[1]
            return redirect(url_for('index'))  # Chuyển hướng đến trang chính
        else:
            # Đăng nhập thất bại, thông báo lỗi
            return "Đăng nhập thất bại! Tên đăng nhập hoặc mật khẩu không đúng."

    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    print("hello")
    session.pop('user_id', None)  # Xóa thông tin người dùng khỏi session
    session.pop('user_login', None)  # Xóa tên người dùng khỏi session
    return redirect(url_for('login'))  # Chuyển hướng về trang đăng nhập

@app.route('/index')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Nếu chưa đăng nhập, chuyển hướng đến trang login

    conn = g.db_connection
    cur = conn.cursor()

    # Lấy danh sách các tiết mục từ bảng vote_festival_model
    cur.execute("SELECT id, name, vote_number FROM vote_festival_model")
    festivals = cur.fetchall()

    # Kiểm tra xem người dùng đã bình chọn chưa
    user_id = session['user_id']
    user_votes = {}
    cur.execute("SELECT vote_festival_model_id FROM vote_festival_model_line WHERE user_id = %s", (user_id,))
    for row in cur.fetchall():
        user_votes[row[0]] = True

    cur.close()

    # Truyền user_votes vào template để kiểm tra và hiển thị nút tương ứng
    return render_template('index.html', festivals=festivals, user_votes=user_votes)

@app.route('/vote', methods=['POST'])
def vote():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    vote_id = request.json.get('vote_id')
    if not vote_id:
        return jsonify({"error": "Invalid request"}), 400

    conn = g.db_connection
    cur = conn.cursor()

    # Kiểm tra xem người dùng đã bình chọn cho tiết mục này chưa
    user_id = session['user_id']
    cur.execute("SELECT * FROM vote_festival_model_line WHERE user_id = %s AND vote_festival_model_id = %s", (user_id, vote_id))
    existing_vote = cur.fetchone()

    if existing_vote:
        # Nếu đã bình chọn, thực hiện bỏ bình chọn
        cur.execute("DELETE FROM vote_festival_model_line WHERE user_id = %s AND vote_festival_model_id = %s", (user_id, vote_id))
        cur.execute("UPDATE vote_festival_model SET vote_number = vote_number - 1 WHERE id = %s", (vote_id,))
        action = 'removed'
    else:
        # Nếu chưa bình chọn, thực hiện bình chọn
        cur.execute("INSERT INTO vote_festival_model_line (user_id, vote_festival_model_id) VALUES (%s, %s)", (user_id, vote_id))
        cur.execute("UPDATE vote_festival_model SET vote_number = vote_number + 1 WHERE id = %s", (vote_id,))
        action = 'added'

    # Cập nhật lại số lượt bình chọn và gửi thông báo cho người dùng hiện tại
    cur.execute("SELECT vote_number FROM vote_festival_model WHERE id = %s", (vote_id,))
    updated_vote_number = cur.fetchone()[0]
    conn.commit()  # Đảm bảo commit sau khi cập nhật dữ liệu

    cur.close()

    # Gửi thông báo tới tất cả các client
    socketio.emit('update_vote', {
        'vote_festival_model_id': vote_id,
        'vote_number': updated_vote_number,
        'action': action
    }, room=None)

    return jsonify({"vote_number": updated_vote_number, "action": action})

# Kết nối người dùng vào phòng khi họ đăng nhập
@socketio.on('join_room')
def on_join(data):
    user_id = data['user_id']
    join_room(str(user_id))
    print(f"User {user_id} joined room.")

# Chạy ứng dụng Flask với Flask-SocketIO
if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
