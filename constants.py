import os
import dash
import redis
from dotenv import load_dotenv

load_dotenv()

BUTTON_STYLE = {
    "width": "80%",
    "margin-top": "10px",
    "backgroundColor": "rgb(28, 126, 214)",
    "color": "white",
    "border": "0px",
    "borderRadius": "5px",
}

MAP_HEIGHT = "475px"
GRID_HEIGHT = "250px"
PANEL_HEIGHT = "325px"

COLUMN_DEFS = [
    {"field": "name", "checkboxSelection": True},
    {"field": "id"},
    {"field": "date"},
    {"field": "lat"},
    {"field": "lon"},
    {"field": "dim"},
    {"field": "classified"},
    {"field": "n classes"},
    {"field": "class distribution"},
]

REDIS_EXPIRE_SEC = 60 * 60 * 2  # Expire data in 2 hours
os.environ["REDIS_URL"] = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379")
redis_instance = redis.StrictRedis.from_url(
    os.environ.get("REDIS_URL", "redis://127.0.0.1:6379")
)

NASA_KEY = os.getenv("NASA")

app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
)

app.title = "Land cover analysis and classification"
