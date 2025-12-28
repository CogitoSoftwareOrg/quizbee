import multiprocessing
import os

# Bind address
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")

# Workers: 2-4 x CPU cores is a common baseline
workers = 2

# Worker class: Uvicorn ASGI worker
worker_class = "uvicorn.workers.UvicornWorker"

# Ensure src-layout package resolution
pythonpath = "src"

# Graceful timeouts
timeout = int(os.getenv("GUNICORN_TIMEOUT", 60))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", 30))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", 5))

# Access and error logs (stdout/stderr by default, or set paths)
accesslog = os.getenv("GUNICORN_ACCESSLOG", "-")
errorlog = os.getenv("GUNICORN_ERRORLOG", "-")
loglevel = os.getenv("GUNICORN_LOGLEVEL", "info")

# Process naming
proc_name = "api"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Worker connections and limits
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Access log format
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'


# Server hooks
def on_starting(server):
    server.log.info("Starting API server")


def on_reload(server):
    server.log.info("Reloading API server")


def worker_int(worker):
    worker.log.info("Worker received INT or QUIT signal")


def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)


def post_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)


def post_worker_init(worker):
    worker.log.info("Worker initialized (pid: %s)", worker.pid)


def worker_abort(worker):
    worker.log.info("Worker aborted (pid: %s)", worker.pid)


def pre_exec(server):
    server.log.info("Forked child, re-executing.")


def when_ready(server):
    server.log.info("Server is ready. Spawning workers")


def worker_exit(server, worker):
    server.log.info("Worker exited (pid: %s)", worker.pid)


def nworkers_changed(server, new_value, old_value):
    server.log.info("Spawning %s workers", new_value)


def on_exit(server):
    server.log.info("Server exiting")
