import base64
import datetime
import json
import os
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from modules.err import err_message
from modules.nsfw import nsfw_probability
from modules.prompt import getprompt
from modules.vision import vision_check

from modules.logger import get_logger
import httpx
import pytz
import requests
from modules.config import load_config
from io import BytesIO
from PIL import Image

from modules.webscript import url2img,check_url

logger = get_logger()
config = load_config()

#서버구분
if os.getenv('APP_ENV'):
    server = os.getenv('APP_ENV')
else:
    server = 'default'

async def txt2img(request):
    try:
        # Get the arguments
        data = json.loads(config['genmodel']['args'])
         # 현재 시간을 KR 시간대로 구합니다.
        utc_now = datetime.datetime.utcnow()
        kst_now = utc_now.replace(tzinfo=pytz.utc).astimezone(pytz.timezone('Asia/Seoul'))

        # 파일 이름
        filename = f"{kst_now.strftime('%Y%m%d%H%M%S')}{kst_now.microsecond}.png"
        
        if await check_url(request['webSiteUrl']):
            # website 이미지 파일을 가져옵니다.
            img = await url2img(request['webSiteUrl'])
        else:
            logger.error(f"[Error]: {request['webSiteUrl']}에 접속할 수 없습니다.")
            return err_message(403,"url이 잘못되었습니다.")
        
        async with httpx.AsyncClient() as client:
            # img2promt api 호출
            img2promt = await client.post(
                config[server]['getimgpromptapi'],
                files={"image": ("script.png", img, "image/png")},
                timeout=httpx.Timeout(30.0, read=30.0)  # 타임아웃 설정을 적용
            )
             
        # prompt 생성
        prompt = await getprompt(config[server]['openaikey'], request['designPrompt'], img2promt.json()['prompt'])
        logger.info(f"Prompt 생성 완료 :{prompt}")
        if prompt is None:
            logger.error(f"[Error]: prompt 생성에 실패하였습니다.")
            return err_message(500,"prompt 생성에 실패하였습니다.")
        
        if request['designPrompt']['pictureSize']=='전신':
            pictureSize ='detailed skin,((full body))' 
        elif request['designPrompt']['pictureSize']=='상반신':
            pictureSize = 'detailed skin,((upper body))'
        elif request['designPrompt']['pictureSize']=='클로즈업':
            pictureSize = '((close up on face))'
        else:
            logger.error(f"[Error]: {request['designPrompt']['pictureSize']}는 사용할 수 없습니다.")
            return err_message(405,"Not Found PictureSize .")
        
        # options settings
        data['model'] = config['genmodel']['model']
        data['prompt'] = prompt + data['prompt'] + pictureSize
        data['sd_vae'] = config['genmodel']['sd_vae']
        data['seed'] = int(request['seed'])
        
        async with httpx.AsyncClient() as client:
            response = await client.post(config[server]['getmodelapi'], json=data, timeout=httpx.Timeout(180.0, read=180.0))
            genmodel = response.json()

        #Tencent CosS3연결
        region = None              # “region” does not need to be specified if you initialize with a custom domain.
        token = None               # Token is required for temporary keys but not permanent keys. For more information about how to generate and use a temporary key, visit https://www.tencentcloud.com/document/product/436/14048
        scheme = 'https'           # Specify whether to use HTTP or HTTPS protocol to access COS. This field is optional and is `https` by default
        domain = 'images-designstaff-ai-1320494403.cos.ap-seoul.myqcloud.com'
        cosconfig = CosConfig(Region=region, SecretId=config[server]['tencent_access_key_id'], SecretKey=config[server]['tencent_secret_access_key'], Token=token, Domain=domain, Scheme=scheme)
        coss3 = CosS3Client(cosconfig)

        #generator image s3 업로드
        images = []
        for index, image_data in enumerate(response.json()['images'],start=0):

            # 이미지의 너비와 높이 가져오기
            img = BytesIO(base64.b64decode(image_data))
            genWidth, genheight = Image.open(img).size
            if nsfw_probability(img):
                logger.error(f"[Error]: NSFW 이미지가 생성되었습니다.")
                return err_message(406,"NSFW 이미지가 생성되었습니다.")
            
            coss3.upload_file_from_buffer(
                Bucket='',
                Body=BytesIO(base64.b64decode(image_data)),
                Key=f'aigenerate/{filename}',
                PartSize=1,
                MAXThread=10,
                EnableMD5=False
            )
            
            images.append(f"{config[server]['model_design_url']}{filename}")

        # 응답 데이터 생성        
        json_data = {
            'designReqId': request['designReqId'],
            'designImageUrl': images[0],
            'positivePrompt': genmodel['parameters']['prompt'],
            'negativePrompt': genmodel['parameters']['negative_prompt'],
            'designWidth': genWidth,
            'designHeight': genheight,
            'seed': json.loads(genmodel['info'])['seed']
        }

        return JSONResponse(status_code=200,content={"status":"succes", "message":"", "data":json_data, "exception":""})
    except Exception as e:
        # 예외가 발생한 경우 에러 메시지를 응답에 포함시켜 반환
        err = {
            "status": "error",
            "message": type(e).__name__ + vars(e).get('detail', ''),
            "data": vars(e).get('body', ''),
            "exception": str(e),
        }
        logger.error(f"[Error]: {err}")
        raise HTTPException(status_code=500, detail=str(e))
