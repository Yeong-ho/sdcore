from fastapi import FastAPI
from modules.api import Api
from modules.call_queue import queue_lock 
import os

from modules.logger import get_logger


logger = get_logger()
app = FastAPI(title=f"{os.getenv('APP_ENV')} B2B SDCORE API",
              description=f"{os.getenv('APP_ENV')} Design Staff B2B SDCORE API", version="1.0.0", background_tasks=True)
api = Api(app,queue_lock)
