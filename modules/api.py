import json
from fastapi import APIRouter, FastAPI,Request,BackgroundTasks
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.encoders import jsonable_encoder
from concurrent.futures import ThreadPoolExecutor
from threading import Lock, Thread
import os

import models.model as model
from modules.config import load_config
from modules.err import err_message
from modules.logger import get_logger
from modules.quetask import BackgroundTask, ModelTask
from modules.vision import vision_check

logger = get_logger()
config = load_config()

#서버구분
if os.getenv('APP_ENV'):
    server = os.getenv('APP_ENV')
else:
    server = 'default'

def api_middleware(app: FastAPI):
    @app.middleware("http")
    async def custom_middleware(request, call_next):
        # API 요청 로그 기록
        logger.info(f"Request received: {request.method} {request.url}")

        response = await call_next(request)
        # API 응답 로그 기록
        logger.info(f"Response: {vars(response).get('status_code')}")
        return response
    
    def handle_exception(request: Request, e: Exception):
        err = {
            "status": "error",
            "message": type(e).__name__+vars(e).get('detail', ''),
            "data": vars(e).get('body', ''),
            "exception": str(e),
        }
        return JSONResponse(status_code=vars(e).get('status_code', 500), content=jsonable_encoder(err))

    @app.middleware("http")
    async def exception_handling(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception as e:
            return handle_exception(request, e)

    @app.exception_handler(Exception)
    async def fastapi_exception_handler(request: Request, e: Exception):
        return handle_exception(request, e)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, e: HTTPException):
        return handle_exception(request, e)


class Api:
    def __init__(self, app: FastAPI,queue_lock : Lock):
        self.app = app
        self.queue_lock = queue_lock
        self.router = APIRouter()
        self.bg_task = BackgroundTask()
        self.model_task = ModelTask()
        api_middleware(self.app)

        #self.app.include_router(self.router)
        self.add_api_route("/genmodel", self.genmodelapi, response_model=model.ReqResponse,methods=["POST"],tags=["TextToImg"])
        self.add_api_route("/genbg", self.genbgapi, response_model=model.ReqResponse,methods=["POST"],tags=["ImgToImg"])
        self.add_api_route("/queuelsit", self.get_queue, methods=["GET"], tags=["GetQueue"])
    

    def add_api_route(self, path: str, endpoint, **kwargs):
        return self.app.add_api_route(path, endpoint, **kwargs)

    async def genmodelapi(self,request: model.Txt2imgRequest,background_tasks: BackgroundTasks):
        task_id = await self.model_task.add_to_queue(request)

        logger.info(f"Gen Model QueADD Task ID[{task_id}]")
        genmodel = await self.model_task.process_queue_item()
        logger.info(f"Gen Model QueEND Task ID[{task_id}]")

        if vars(genmodel).get('status_code') != 200:
            return genmodel
        
        # body 데이터 디코딩 및 JSON 파싱
        body_data = json.loads(vars(genmodel)['body'].decode('utf-8'))

        # 저작권 체크 호출
        background_tasks.add_task(vision_check,config[server]['vision_save_url'],request.designReqId,[{"imageUrl":body_data['data']['designImageUrl']}],logger)  #백그라운드로 실행
        return model.ReqResponse(status="success", message=f"{task_id}", data=body_data['data'], exception="")


    async def genbgapi(self,request: model.Img2imgRequest,background_tasks: BackgroundTasks):
        task_id = await self.bg_task.add_to_queue(request)

        logger.info(f"Gen BG QueADD Task ID[{task_id}]")
        gembg = await self.bg_task.process_queue_item()
        logger.info(f"Gen BG QueEND Task ID[{task_id}]")

        # 저작권 체크 호출
        background_tasks.add_task(vision_check,config[server]['vision_save_url'],request.designReqId,gembg['design']['images'],logger)#백그라운드로 실행

        return model.ReqResponse(status="success", message=f"{task_id}", data=gembg, exception="")

    async def get_queue(self,name: str):
        if name == 'bg':
            queue_list = await self.bg_task.get_queue_list()
        elif name == 'model':
            queue_list = await self.model_task.get_queue_list()
        else:
            logger.info(f"Get Queue : No such queue name")
            return "No such queue name"
        return {"queue_content": queue_list}