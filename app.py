import dash
import dash_design_kit as ddk
from dash import dcc, html, Input, Output, State
import plotly.express as px
import dash_leaflet as dl
from datetime import date
import dash_mantine_components as dmc
import dash_ag_grid as dag
from dash_extensions.javascript import assign
from utils.data_utils import get_image, update_df, to_geojson
import warnings
import pickle
from constants import redis_instance

# Temporary -- muting pandas warnings for using df.append()
warnings.simplefilter(action="ignore", category=FutureWarning)

button_style = {"width": "80%", "margin": "15px"}

app = dash.Dash(__name__)
app.title = "Land cover analysis and classification"
server = app.server  # expose server variable for Procfile

df = update_df()

columnDefs = [
    {"field": "id", "checkboxSelection": True},
    {"field": "date"},
    {"field": "lat"},
    {"field": "lon"},
    {"field": "dim"},
]

app.layout = dmc.NotificationsProvider(
    ddk.App(
        [
            ddk.Header(
                [
                    ddk.Logo(src=app.get_asset_url("plotly_logo.png")),
                    ddk.Title("Land cover analysis and classification"),
                ]
            ),
            ddk.Row(
                children=[
                    ddk.ControlCard(
                        width=30,
                        children=[
                            ddk.CardHeader(title="Data access"),
                            dmc.Space(h=30),
                            ddk.ControlItem(
                                label="Dim",
                                children=dcc.Slider(
                                    id="img-dim",
                                    min=0,
                                    max=1,
                                    step=0.1,
                                    value=0.1,
                                    marks=None,
                                    tooltip={
                                        "placement": "bottom",
                                        "always_visible": True,
                                    },
                                ),
                            ),
                            ddk.ControlItem(
                                label="Date",
                                children=dmc.DatePicker(
                                    id="my-date-picker",
                                    minDate=date(2015, 8, 5),
                                    value=date(2020, 8, 5),
                                ),
                            ),
                            ddk.ControlItem(
                                label="Latitude",
                                children=dcc.Input(
                                    id="lat",
                                    min=-90,
                                    max=90,
                                    value=50.23,
                                    type="number",
                                ),
                            ),
                            ddk.ControlItem(
                                label="Longitude",
                                children=dcc.Input(
                                    id="lon",
                                    min=-180,
                                    max=180,
                                    value=-120,
                                    type="number",
                                ),
                            ),
                            dmc.Space(h=50),
                            html.Button("Download image", id="get-data"),
                        ],
                        style={"height": "550px"},
                    ),
                    ddk.Block(
                        style={"margin": "15px"},
                        width=70,
                        children=[
                            html.Div(
                                dl.Map(
                                    id="map-view",
                                    center=[38.0, -95.0],
                                    zoom=4,
                                    minZoom=2,
                                    children=[
                                        dl.TileLayer(
                                            url="https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png",
                                            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, Tiles style by <a href="https://www.hotosm.org/" target="_blank">Humanitarian OpenStreetMap Team</a> hosted by <a href="https://openstreetmap.fr/" target="_blank">OpenStreetMap France</a>',
                                        ),
                                        dl.GestureHandling(),
                                        dl.LayersControl(
                                            [
                                                dl.BaseLayer(
                                                    name="Study areas",
                                                    checked=True,
                                                    children=dl.GeoJSON(
                                                        data=to_geojson(df),
                                                        id="geojson",
                                                    ),
                                                ),
                                                dl.Overlay(
                                                    name="Satellite image",
                                                    checked=True,
                                                    id="satellite-img",
                                                ),
                                            ]
                                        ),
                                        dl.FeatureGroup(
                                            [dl.EditControl(id="edit_control")]
                                        ),
                                    ],
                                    style={
                                        "width": "100%",
                                        "height": "550px",
                                        "margin": "auto",
                                        "display": "block",
                                    },
                                )
                            )
                        ],
                    ),
                ]
            ),
            ddk.Card(
                children=[
                    ddk.CardHeader(title="Select imagery to view"),
                    ddk.Row(
                        [
                            ddk.Block(
                                width=80,
                                children=[
                                    dmc.LoadingOverlay(
                                        dag.AgGrid(
                                            id="image-options",
                                            columnDefs=columnDefs,
                                            rowData=df.to_dict("records"),
                                            columnSize="sizeToFit",
                                            defaultColDef=dict(
                                                resizable=True,
                                            ),
                                            style={"height": "250px"},
                                        )
                                    ),
                                ],
                            ),
                            ddk.Block(
                                width=20,
                                children=[
                                    dmc.Center(
                                        html.Button(
                                            "Display image",
                                            id="display",
                                            style=button_style,
                                        ),
                                    ),
                                    dmc.Center(
                                        html.Button(
                                            "Start analysis",
                                            id="classify",
                                            style=button_style,
                                        ),
                                    ),
                                    dmc.Center(
                                        html.Button(
                                            "Delete selection",
                                            id="delete",
                                            style=button_style,
                                        )
                                    ),
                                ],
                            ),
                        ]
                    ),
                    html.Div(id="delete-div"),
                    html.Div(id="display-div"),
                ],
                style={"height": "350px"},
            ),
            html.Div(id="notify-container"),
        ]
    ),
    autoClose=10000,
)


@app.callback(
    Output("satellite-img", "children"),
    Input("display", "n_clicks"),
    State("image-options", "selectedRows"),
)
def display_image(n_clicks, selection):
    if n_clicks and selection:
        img_id = selection[0]["id"]
        lat = float(selection[0]["lat"])
        lon = float(selection[0]["lon"])
        dim = float(selection[0]["dim"])
        img = pickle.loads(redis_instance.get(img_id))

        image_bounds = [
            [(lat - (dim / 2)), (lon - ((dim / 2)))],
            [(lat + (dim / 2)), (lon + ((dim / 2)))],
        ]

        return (
            dl.LayerGroup(
                dl.ImageOverlay(
                    opacity=0.95,
                    url=img,
                    bounds=image_bounds,
                )
            ),
        )


# TODO: Finish and merge with bigger callback
@app.callback(
    Output("delete-div", "children"),
    Input("delete", "n_clicks"),
    State("image-options", "selectedRows"),
)
def delete_img(n_clicks, selection):
    if n_clicks:
        print(selection)
        return selection
    return dash.no_update


@app.callback(
    Output("map-view", "center"),
    Output("map-view", "zoom"),
    Input("image-options", "selectedRows"),
)
def zoom_map(selection):
    if selection:
        return (float(selection[0]["lat"]), float(selection[0]["lon"])), 8
    return dash.no_update


@app.callback(
    Output("notify-container", "children"),
    Output("image-options", "rowData"),
    Output("geojson", "data"),
    Input("get-data", "n_clicks"),
    State("my-date-picker", "value"),
    State("lat", "value"),
    State("lon", "value"),
    State("img-dim", "value"),
    prevent_initial_call=True,
)
def loc_data(n_clicks, date, lat, lon, dim):
    if n_clicks:
        msg = get_image(lat, lon, dim, date)
        df = update_df()
        return (
            dmc.Notification(id="update", action="show", message=msg),
            df.to_dict("records"),
            to_geojson(df),
        )
    return dash.no_update, dash.no_update, dash.no_update


# @app.callback(
#     Output("image-options", "rowData"), Input("get-data", "n_clicks")
# )
# def get_download_options(nclicks):
#     if nclicks:
#         print("get data!")
#     return dash.no_update


if __name__ == "__main__":
    app.run_server(debug=True)
