import asyncio
import json
import time
import uuid
from fastapi import BackgroundTasks
from fastapi.encoders import jsonable_encoder

from modules.img2img import img2img
from modules.logger import get_logger
from modules.txt2img import txt2img

logger=get_logger()

class BackgroundTask:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(1)

    async def add_to_queue(self, request_data):
        task_id = str(uuid.uuid4())
        await self.queue.put((task_id, request_data))
        return task_id

    async def process_queue_item(self):
        while not self.queue.empty():
            async with self.semaphore:
                task_id, request_data = await self.queue.get()
                logger.info(f"(Gen Background START) Task ID[{task_id}]")
                # 요청 처리 로직을 여기에 추가
                result = await img2img(jsonable_encoder(request_data))
                return result

    async def get_queue_list(self):
        return list(self.queue._queue)

class ModelTask:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.semaphore = asyncio.Semaphore(1)

    async def add_to_queue(self, request_data):
        task_id = str(uuid.uuid4())
        await self.queue.put((task_id, request_data))
        return task_id

    async def process_queue_item(self):
        while not self.queue.empty():
            async with self.semaphore:
                task_id, request_data = await self.queue.get()
                logger.info(f"(Gen Model START) Task ID[{task_id}]")
                # 요청 처리 로직을 여기에 추가
                result = await txt2img(jsonable_encoder(request_data))
                return result
            
    async def get_queue_list(self):
        return list(self.queue._queue)
