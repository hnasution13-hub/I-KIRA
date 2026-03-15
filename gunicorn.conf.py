# Gunicorn configuration untuk production
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = 1
threads = 2
worker_class = "gthread"
worker_connections = 1000
timeout = 120
keepalive = 2

# Restart workers setelah n requests (mencegah memory leak)
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "hris_smartdesk"

# Server mechanics
daemon = False
pidfile = None
