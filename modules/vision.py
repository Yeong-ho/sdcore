import time
from google.cloud import vision

import logging
from models.model import ImageEntity, ImageLabel
import requests
import base64
import asyncio
import json

import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'desigstaff-8cb40729117a.json'


def vision_check(url,id,images,logger):
    image_list: ImageEntity = ImageEntity()
    time.sleep(3)
    try:
        for index, image_data in enumerate(images, start=1):
            image_list = detect_web_uri(id,image_data['imageUrl'])
            imageLabelList = []
            for index in vars(image_list)['imageLabelList']:
                imageLabelList.append({"score":index.score,"description":index.description})

            json_data = {
                "designReqId": id,
                "orgImageUrl": image_data['imageUrl'],
                "bestGuess": vars(image_list)['bestGuessLabel'],
                "imageLabelList":imageLabelList,
                "partialMatchingImages":vars(image_list)['partialMatchingImages'],
                "fullMatchingImages":vars(image_list)['fullMatchingImages'],
                "similarImages":vars(image_list)['similarImages']
            }
            requests.post(url,json=json_data)
    except Exception as error:
        logger.error(f"[Error]: copyright_condition 체크에 실패하였습니다.: {str(error)}")

def get_image_content_from_url(image_url):
    try:
        # 이미지 URL에서 이미지 다운로드
        response = requests.get(image_url)
        response.raise_for_status()  # 에러 체크

        # 다운로드한 이미지를 바이너리 형태의 content로 변환
        content = response.content

        return content

    except requests.exceptions.RequestException as e:
        print(f"Failed to download image: {e}")
        return None


def detect_web_uri(id,uri) -> ImageEntity:
    client = vision.ImageAnnotatorClient()

    content = get_image_content_from_url(uri)

    image = vision.Image(content=content)

    client = client.from_service_account_json('desigstaff-8cb40729117a.json')
    response = client.web_detection(image=image)
    
    annotations = response.web_detection
    image_entity: ImageEntity = ImageEntity(designReqId=id ,bestGuessLabel='', imageLabelList=[], partialMatchingImages=[],
                                            fullMatchingImages=[], similarImages=[])
    if annotations.full_matching_images:
        for image in annotations.full_matching_images:
            image_entity.fullMatchingImages.append(image.url)

    if annotations.partial_matching_images:
        for image in annotations.partial_matching_images:
            image_entity.partialMatchingImages.append(image.url)

    if annotations.best_guess_labels:
        for label in annotations.best_guess_labels:
            image_entity.bestGuessLabel = label.label

    if annotations.web_entities:
        for entity in annotations.web_entities:
            image_entity.imageLabelList.append(ImageLabel(score=entity.score, description=entity.description))

    if annotations.visually_similar_images:
        for image in annotations.visually_similar_images:
            image_entity.similarImages.append(image.url)


    return image_entity


