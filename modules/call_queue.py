from functools import wraps
import html
import threading
import time

queue_lock = threading.Lock()
