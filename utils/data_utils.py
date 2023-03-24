import requests
import PIL
import io
import pickle
from constants import redis_instance, REDIS_EXPIRE_SEC, NASA_KEY
import json
import pandas as pd


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
        if img_id in [x.decode("utf8") for x in redis_instance.keys()]:
            print("Image already stored in redis. Loading from cache.")
            img = pickle.loads(redis_instance.get(img_id))
            return img
        else:
            print("Retrieving image data from API...")
            img_data = requests.get(img_url).content
            image_bytes = io.BytesIO(img_data)
            img = PIL.Image.open(image_bytes)
            img_info = {
                "lat": lat,
                "lon": lon,
                "dim": dim,
                "date": date,
                "id": img_id,
            }

            redis_instance.set(img_id, pickle.dumps(img))
            redis_instance.set(f"{img_id}_metadata", pickle.dumps(img_info))
            redis_instance.expire(img_id, REDIS_EXPIRE_SEC)
            redis_instance.expire(f"{img_id}_metadata", REDIS_EXPIRE_SEC)

            print("Image data successfully retrieved and stored in Redis.")
            return img


def update_df(df=None):
    df = (
        pd.DataFrame(columns=["id", "date", "lat", "lon", "dim"])
        if not df
        else df
    )
    for key in redis_instance.keys("*_metadata"):
        df = df.append(
            pickle.loads(redis_instance.get(key)), ignore_index=True
        )
    return df
