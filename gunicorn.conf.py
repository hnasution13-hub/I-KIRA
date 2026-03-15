# Gunicorn configuration — optimized untuk Render free tier (512MB RAM)
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 64

# Worker — 1 worker saja untuk free tier 512MB
workers = 1
threads = 2
worker_class = "gthread"
worker_connections = 100
timeout = 120
keepalive = 2

# Restart worker setelah n requests (cegah memory leak)
max_requests = 500
max_requests_jitter = 50

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "warning"
access_log_format = '%(h)s %(r)s %(s)s %(b)s %(D)s'

# Process naming
proc_name = "ikira_hris"

# Server mechanics
daemon = False
pidfile = None