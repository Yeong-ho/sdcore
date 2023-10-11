from langchain.llms import OpenAI
from langchain import PromptTemplate, LLMChain
import os
import json

# Prompt 템플릿 생성 함수
async def create_stablediffusion_prompt(age, gender, concept, focus, additional,siteconcept):
    template = f"""
    Age: {age}
    Gender: {gender}
    Concept: {concept}
    Focus: {focus}
    Additional: {additional}
    Siteconcept: {siteconcept}

    Please create a stable spread prompt by referring to age, gender, concept, focus, additional information, site concept, etc. Please create a creative spread prompt by referring to age, gender, concept, focus, additional information, and site concept.
    Question: {{question}}
    """
    input_variables = ["question"]
    return PromptTemplate(template=template, input_variables=input_variables)

# Prompt 생성
async def getprompt(key,value,siteconcept):
  try :
    os.environ["OPENAI_API_KEY"] = key
    # LLM 초기화
    llm = OpenAI(temperature=0.1,model_name="text-davinci-003")

    age = value['age']
    gender = value['gender']
    concept = ", ".join(value['concept'])
    focus = value['pictureSize']# "full body" #upper body #close-up portrait
    additional = value['description']
    
    # Prompt 템플릿 생성
    template = await create_stablediffusion_prompt(age, gender, concept, focus, additional,siteconcept)
    # LLMChain 초기화 및 실행
    llm_chain = LLMChain(prompt=template, llm=llm)

    # 질문 실행
    result = llm_chain.run("Please extract only the prompt from the JSON you made as a result and provide it. please english")
    return result.split("Prompt:")[-1].replace("\n","")
  except Exception as e:
    return None