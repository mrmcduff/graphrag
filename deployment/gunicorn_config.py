"""
Gunicorn configuration file for GraphRAG API server.
"""

# The socket to bind
bind = "127.0.0.1:8000"

# Number of worker processes
workers = 4

# Number of threads per worker
threads = 2

# Maximum requests before worker restart
max_requests = 1000
max_requests_jitter = 50

# Process name
proc_name = "graphrag_api"

# Logging
accesslog = "/var/log/graphrag/access.log"
errorlog = "/var/log/graphrag/error.log"
loglevel = "info"

# Timeout (in seconds)
timeout = 120
