# Gunicorn configuration file for Flask + SocketIO
# Chạy: gunicorn -c gunicorn_config.py app:app

import multiprocessing

# Bind address
bind = "0.0.0.0:5000"

# Worker configuration
# Số workers = (2 * CPU cores) + 1
workers = multiprocessing.cpu_count() * 2 + 1

# Sử dụng gevent cho WebSocket support
worker_class = "geventwebsocket.gunicorn.workers.GeventWebSocketWorker"

# Số connections mỗi worker có thể xử lý
worker_connections = 1000

# Timeout (seconds)
timeout = 120

# Keep alive
keepalive = 5

# Logging
accesslog = "access.log"
errorlog = "error.log"
loglevel = "info"

# Reload khi code thay đổi (chỉ dùng cho development)
reload = False

# Process naming
proc_name = "vote_flask"

# Preload app để tiết kiệm memory
preload_app = True
