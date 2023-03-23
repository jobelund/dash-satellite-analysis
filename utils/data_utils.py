import requests
import PIL
import io
import pickle
from constants import redis_instance, REDIS_EXPIRE_SEC, NASA_KEY
import json


def get_image(lat, lon, dim, date="2014-02-04"):
    img_url = f"https://api.nasa.gov/planetary/earth/imagery?lon={lon}&lat={lat}&date={date}&dim={dim}&api_key={NASA_KEY}"
    asset_url = f"https://api.nasa.gov/planetary/earth/assets?lon={lon}&lat={lat}&date={date}&dim={dim}&api_key={NASA_KEY}"
    img_metadata = json.loads(requests.get(asset_url).content)

    if "msg" in img_metadata.keys():
        print(img_metadata["msg"])
        print(asset_url)
        return None
    elif "id" in img_metadata.keys():
        img_id = img_metadata["id"]
        if img_id in [x.decode('utf8') for x in redis_instance.keys()]:
            print("Image already stored in redis. Loading from cache.")
            img = pickle.loads(redis_instance.get(img_id))
            return img
        else:
            print("Retrieving image data from API...")
            img_data = requests.get(img_url).content
            image_bytes = io.BytesIO(img_data)
            img = PIL.Image.open(image_bytes)
            redis_instance.set(id=img_id, value=pickle.dumps(img))
            redis_instance.expire(img_id, REDIS_EXPIRE_SEC)
            print("Image data successfully retrieved and stored in Redis.")
            return img