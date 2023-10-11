import requests
from PIL import Image
import opennsfw2 as n2
import asyncio
import aiohttp

def nsfw_probability(image):
    return 0.8<n2.predict_image(image)
