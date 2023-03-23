import os
import dash
import redis

REDIS_EXPIRE_SEC = 60 * 60 * 2  # Expire data in 2 hours
os.environ["REDIS_URL"] = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379")
redis_instance = redis.StrictRedis.from_url(
    os.environ.get("REDIS_URL", "redis://127.0.0.1:6379")
)

IMG_DIM = 0.1  # X and Y dimensions of the satellite image to return from the NASA API
NASA_KEY = os.getenv("NASA")

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
)

app.title = "Land cover analysis and classification"
