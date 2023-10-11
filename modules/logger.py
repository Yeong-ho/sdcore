import logging
from logging.handlers import TimedRotatingFileHandler
import os
import datetime
import pytz

def get_logger():
    # 로그 생성
    logger = logging.getLogger("SDCore")  # 로거 이름을 지정하여 고유하게 만듭니다.
    if not logger.handlers:  # 핸들러가 이미 추가되었는지 확인
        # 로그의 출력 기준 설정
        logger.setLevel(logging.INFO)

        # log 출력 형식
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        kst = pytz.timezone('Asia/Seoul')  # 한국 시간대 설정

        # log를 콘솔에 출력
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        # log를 날짜별로 분리하여 파일에 출력
        log_folder = 'logs'
        if not os.path.exists(log_folder):
            os.makedirs(log_folder)

        log_file = os.path.join(log_folder, 'main.log')
        file_handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7)
        file_handler.suffix = "%Y-%m-%d.log"  # 날짜별로 분리된 파일 이름 형식
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
    
    return logger
