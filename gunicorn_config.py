# Gunicorn configuration file for Flask
# Chạy: gunicorn -c gunicorn_config.py app:app

import multiprocessing

# Bind address
bind = "0.0.0.0:5000"

# Worker configuration
workers = multiprocessing.cpu_count() * 2 + 1

# Use sync workers (no longer need gevent for websocket)
worker_class = "sync"

# Threads per worker
threads = 2

# Timeout (seconds)
timeout = 120

# Keep alive
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Reload khi code thay đổi (development only)
reload = False

# Process naming
proc_name = "vote_flask"
