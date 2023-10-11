
import platform
import requests
from selenium.common.exceptions import InvalidArgumentException

from fastapi import HTTPException

async def url2img(url):
    try: 
        if platform.system() == "Linux":  # 리눅스

            from selenium import webdriver
            from pyvirtualdisplay import Display
            from io import BytesIO
            from PIL import Image

            # 가상 디스플레이 생성
            display = Display(visible=0, size=(786, 1536))
            display.start()

            # 웹 드라이버 초기화
            options = webdriver.ChromeOptions()
            options.add_argument("--no-sandbox")  # 리눅스에서 실행할 때 보안 관련 이슈를 해결하기 위
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--headless")  # GUI 없는 환경에서 실행
            options.add_argument(f"--window-size={786},{1536}")  # 브라우저 창 크기 설정
            driver = webdriver.Chrome(options=options)

            # 웹 페이지 열기
            driver.get(url)

            # 스크린샷 캡처
            screenshot_bytes = driver.get_screenshot_as_png()

            # BytesIO에 이미지 데이터 저장
            img_buffer = BytesIO(screenshot_bytes)

            # 웹 드라이버 종료 및 가상 디스플레이 정리
            driver.quit()
            display.stop()
            return img_buffer
        
        
        else:
            from selenium import webdriver
            from io import BytesIO
            from PIL import Image

            # 웹 드라이버 초기화
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")  # GUI 없는 환경에서 실행
            options.add_argument(f"--window-size={786},{1536}")  # 브라우저 창 크기 설정
            driver = webdriver.Chrome(options=options)

            # 웹 페이지 열기
            driver.get(url)

            # 스크린샷 캡처
            screenshot_bytes = driver.get_screenshot_as_png()

            # BytesIO에 이미지 데이터 저장
            img_buffer = BytesIO(screenshot_bytes)

            # 웹 드라이버 종료
            driver.quit()

            return img_buffer
    except InvalidArgumentException as e:
        # InvalidArgumentException 예외 처리 시 400 에러 리턴
        raise HTTPException(status_code=400, detail=".")
    except Exception as e:
        # 다른 예외 처리
        raise HTTPException(status_code=500, detail="스크린샷 캡처에 실패하였습니다.")

def validate_url(url):
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url  # 스킴이 누락된 경우 "https://"를 추가합니다.
    return url

async def check_url(url):
    try:
        response = requests.head(validate_url(url))
        if response.status_code == 200 or response.status_code == 403 or response.status_code == 410:
            return True
        else:
            return False
    except requests.ConnectionError:
        return False
