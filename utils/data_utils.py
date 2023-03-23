import requests
import PIL
import io
from dotenv import load_dotenv
import pickle
from constants import redis_instance, REDIS_EXPIRE_SEC, NASA_KEY, IMG_DIM


def get_image(lat, lon, date="2014-02-04"):
    img_url = f"https://api.nasa.gov/planetary/earth/imagery?lon={lon}&lat={lat}&date={date}&dim={IMG_DIM}&api_key={NASA_KEY}"
    print(img_url)
    img_data = requests.get(img_url).content
    try:
        image_bytes = io.BytesIO(img_data)
        img = PIL.Image.open(image_bytes)
        redis_instance.set("landsat_img", pickle.dumps(img))
        redis_instance.expire("landsat_img", REDIS_EXPIRE_SEC)
        return img
    except Exception as e:
        print("Image is not available for the specified date or location.")
        return None
