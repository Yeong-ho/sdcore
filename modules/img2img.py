import base64
import datetime
import json
import os
from fastapi import FastAPI, File, HTTPException, BackgroundTasks, UploadFile
from fastapi.responses import JSONResponse

from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from modules.err import err_message
from modules.prompt import getprompt
from modules.vision import vision_check
from modules.config import load_config
from modules.logger import get_logger
import httpx
import pytz
import requests

from io import BytesIO
from PIL import Image

logger = get_logger()
config = load_config()

#서버구분
if os.getenv('APP_ENV'):
    server = os.getenv('APP_ENV')
else:
    server = 'default'

background_tasks = BackgroundTasks()

async def img2img(request):
    try:
        # 현재 시간을 KR 시간대로 구합니다.
        utc_now = datetime.datetime.utcnow()
        kst_now = utc_now.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Asia/Seoul'))

        # 파일 이름
        filename = f"{kst_now.strftime('%Y%m%d%H%M%S')}{kst_now.microsecond}.png"

        # 이미지의 가로 세로 길이를 구합니다.
        image_width, image_height = Image.open(BytesIO(requests.get(request['imageUrl']).content)).size


        data = json.loads(config[server]['genbg_args'])
        data['init_images'] = [request['imageUrl']]
        data['seed'] = int(request['seed'])

        #숲속 : T0001 / 잔잔한물 : T0002 ~ 0006
        # data['prompt'] = data['prompt']+config['catagory'][request.category]

        if request['category'] == '숲속':
            data['prompt'] = data['prompt'] +f",over the dense forest"
        elif request['category'] == '잔잔한 물':
            data['prompt'] = data['prompt'] +f",above the rippling water"
        elif request['category'] == '시원한 물':
            data['prompt'] = data['prompt'] +f",realistic splashing water droplets"
        elif request['category'] == '겨울':
            data['prompt'] = data['prompt'] +f",buried in snow, on the snow"
        elif request['category'] == '대리석':
            data['prompt'] = data['prompt'] +f",placed on a marble shelf, a window"
        elif request['category'] == '나무':
            data['prompt'] = data['prompt'] +f",placed on a wooden shelf, a window"

        #Tencent CosS3연결
        region = None              # “region” does not need to be specified if you initialize with a custom domain.
        token = None               # Token is required for temporary keys but not permanent keys. For more information about how to generate and use a temporary key, visit https://www.tencentcloud.com/document/product/436/14048
        scheme = 'https'           # Specify whether to use HTTP or HTTPS protocol to access COS. This field is optional and is `https` by default
        domain = 'images-designstaff-ai-1320494403.cos.ap-seoul.myqcloud.com'
        cosconfig = CosConfig(Region=region, SecretId=config[server]['tencent_access_key_id'], SecretKey=config[server]['tencent_secret_access_key'], Token=token, Domain=domain, Scheme=scheme)
        coss3 = CosS3Client(cosconfig)

        #generator api호출
        async with httpx.AsyncClient() as client:
            # img2promt api 호출
            response = await client.post(
                config[server]['getgenbgapi'],
                json=data,
                timeout=httpx.Timeout(180.0, read=180.0)  # 타임아웃 설정을 적용
        )
        params = response.json()['parameters']

        #generator image s3 업로드
        images = []
        for index, image_data in enumerate(response.json()['images'],start=0):
            coss3.upload_file_from_buffer(
                Bucket='',
                Body=BytesIO(base64.b64decode(image_data)),
                Key=f'aigenerate/bggen{index}_{filename}',
                PartSize=1,
                MAXThread=10,
                EnableMD5=False
            )

            images.append({"fileName":f"bggen{index}_{filename}","imageUrl":f"{config[server]['bg_design_url']}bggen{index}_{filename}","seed":str(params['seed']+index)})
            
        # 응답 데이터 생성
        json_data = {
            "designReqId": request['designReqId'],
            "design" :{
            "images": images     
            },
            "height": image_height,
            "width": image_width,
            "positivePrompt": params['prompt'],
            "negativePrompt": params['negative_prompt'],
        }
        return json_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))