import dash
import dash_design_kit as ddk
from dash import dcc, html, Input, Output, State
import plotly.express as px
import dash_leaflet as dl
from datetime import date
import dash_mantine_components as dmc
import dash_ag_grid as dag
from dash_extensions.javascript import assign
from utils.data_utils import get_image, update_df
import warnings
import dash_leaflet.express as dlx

# Temporary -- muting pandas warnings for using df.append()
warnings.simplefilter(action="ignore", category=FutureWarning)


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

app.layout = ddk.App(
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
                                                    data=dlx.dicts_to_geojson(
                                                        df.rename(
                                                            columns={
                                                                "id": "tooltip"
                                                            }
                                                        ).to_dict("records")
                                                    ),
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
                        dag.AgGrid(
                            id="image-options",
                            columnDefs=columnDefs,
                            rowData=df.to_dict("records"),
                            columnSize="sizeToFit",
                            defaultColDef=dict(
                                resizable=True,
                            ),
                        ),
                    ]
                ),
                dmc.Space(h=30),
                dmc.Center(
                    [
                        html.Button("Delete selection", id="delete"),
                        html.Button("Display image", id="display"),
                    ]
                ),
                html.Div(id="delete-div"),
                html.Div(id="display-div"),
            ],
            style={"height": "550px"},
        ),
    ]
)


# Get selected location data from the edit control to the geojson component.
# @app.callback(
#     Output("geojson", "data"),
#     Input("edit_control", "geojson"),
#     prevent_initial_call=True,
# )
# def loc_data(geojson):
#     return geojson


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
        print(selection[0]["lat"])
        print(selection[0]["lon"])
        return (float(selection[0]["lat"]), float(selection[0]["lon"])), 8
    return dash.no_update


@app.callback(
    Output("satellite-img", "children"),
    Output("image-options", "rowData"),
    Input("get-data", "n_clicks"),
    State("my-date-picker", "value"),
    State("lat", "value"),
    State("lon", "value"),
    State("img-dim", "value"),
    prevent_initial_call=True,
)
def loc_data(n_clicks, date, lat, lon, dim):
    if n_clicks:
        image = get_image(lat, lon, dim, date)
        image_bounds = [
            [(lat - (dim / 2)), (lon - ((dim / 2)))],
            [(lat + (dim / 2)), (lon + ((dim / 2)))],
        ]
        if image:
            img_overlay = (
                dl.LayerGroup(
                    dl.ImageOverlay(
                        opacity=0.95,
                        url=image,
                        bounds=image_bounds,
                    )
                ),
            )
            df = update_df()
            return img_overlay, df.to_dict("records")
        else:
            return (
                dcc.Markdown(
                    "Image is not available for the specified date or location."
                ),
                dash.no_update,
            )
    else:
        return dash.no_update, dash.no_update


# @app.callback(
#     Output("image-options", "rowData"), Input("get-data", "n_clicks")
# )
# def get_download_options(nclicks):
#     if nclicks:
#         print("get data!")
#     return dash.no_update


if __name__ == "__main__":
    app.run_server(debug=True)
