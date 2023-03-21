import os
import dash


app = dash.Dash(
    __name__,
    suppress_callback_exceptions=True,
)

app.title = "Land cover analysis and classification"
