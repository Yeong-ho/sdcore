from pydantic import BaseModel, Field, create_model
from typing import Dict, List
from typing import Optional

class Txt2imgRequest(BaseModel):
    designReqId: int = Field(..., description="User ID")
    webSiteUrl: str = Field(..., description="webSite URL")
    designPrompt: dict = Field(..., description="Design Prompt")
    seed: str = Field(..., description="Design Seed")

class Img2imgRequest(BaseModel):
    designReqId: int = Field(..., description="User ID")
    webSiteUrl: str = Field(..., description="webSite URL")
    designPrompt: dict = Field(None, description="Design Prompt")
    category : str = Field(..., description="Category")
    seed: str = Field(..., description="Design Seed")
    imageUrl : str = Field(..., description="Image URL")


class ReqResponse(BaseModel):
    status: str = Field(..., description="Status of the request")
    message: str = Field(..., description="Message of the request")
    data: dict = Field(..., description="Data of the request")
    exception: str = Field(..., description="Exception of the request")

class ImageLabel(BaseModel):
    """
      Google Vision Api 를 통해서 이미지를 웹에 검색해서 나온결과물을 담는 모델입니다.
      초기화 없이 자바에 리턴해줄때 사용하므로 Optional로 선언합니다.

      Parameters:
          score (float): 스코어 값 0~?? 사이의 값 높을수록 수치가 강함
          description (str): 스코어에 대한 기준을 표기할 명칭

      """
    score: Optional[float] = None
    description: Optional[str] = None    

class ImageEntity(BaseModel):
    """
            Google Vision Api 를 통해서 이미지를 웹에 검색해서 나온결과물을 담는 모델입니다.
            초기화 없이 자바에 리턴해줄때 사용하므로 Optional로 선언합니다.

            Parameters:
            bestGuessLabel (str): 가장 유사한 이미지의 라벨
            imageLabelList (List[ImageLabel]): 이미지의 라벨 리스트
            partialMatchingImages (list): 부분적으로 일치하는 이미지 리스트
            fullMatchingImages (list): 전체적으로 일치하는 이미지 리스트
            similarImages (list): 유사한 이미지 리스트
    """
    designReqId: Optional[int] = None
    bestGuessLabel: Optional[str] = None
    imageLabelList: Optional[List[ImageLabel]] = None
    partialMatchingImages: Optional[list] = None
    fullMatchingImages: Optional[list] = None
    similarImages: Optional[list] = None
