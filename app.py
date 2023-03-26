import dash
import dash_design_kit as ddk
from dash import dcc, html, Input, Output, State
import dash_leaflet as dl
from datetime import date
import dash_mantine_components as dmc
import dash_ag_grid as dag
from dash_extensions.javascript import assign
from utils.data_utils import *
import warnings
import pickle
from constants import redis_instance
from utils.layout_utils import analysis_modal

# Temporary -- muting pandas warnings for using df.append()
warnings.simplefilter(action="ignore", category=FutureWarning)

button_style = {"width": "80%", "margin": "5px"}

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
    {"field": "classified"},
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
                                                dl.Overlay(
                                                    name="Classified image",
                                                    checked=True,
                                                    id="classified-img",
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
                                            "Display on map",
                                            id="display",
                                            style=button_style,
                                        ),
                                    ),
                                    dmc.Center(
                                        html.Button(
                                            "Crop",
                                            id="crop",
                                            style=button_style,
                                        ),
                                    ),
                                    dmc.Center(
                                        html.Button(
                                            "Classify",
                                            id="classify",
                                            style=button_style,
                                        ),
                                    ),
                                    dmc.Center(
                                        html.Button(
                                            "View detail",
                                            id="summary",
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
            html.Div(id="display-notify"),
            html.Div(id="analyze-notify"),
            html.Div(id="analyze-run-notify"),
            html.Div(id="delete-notify"),
            dmc.Modal(
                title="Configure Image Analysis",
                id="analyze-modal",
                size="40%",
                zIndex=10000,
                overlayOpacity=0.3,
            ),
        ]
    ),
    autoClose=5000,
    position="top-right",
)


@app.callback(
    Output("analyze-modal", "opened"),
    Output("analyze-modal", "children"),
    Output("analyze-notify", "children"),
    Input("classify", "n_clicks"),
    State("analyze-modal", "opened"),
    State("image-options", "selectedRows"),
)
def analyze_image_modal(n_clicks, opened, selected):
    if n_clicks and selected:
        return not opened, analysis_modal(), dash.no_update
    if n_clicks and not selected:
        return (
            dash.no_update,
            dash.no_update,
            dmc.Notification(
                id="error-display",
                action="show",
                message="Please select an image from the table.",
            ),
        )
    return dash.no_update, dash.no_update, dash.no_update


@app.callback(
    Output("satellite-img", "children"),
    Output("classified-img", "children"),
    Output("display-notify", "children"),
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

        layer_img = dl.LayerGroup(
            dl.ImageOverlay(
                opacity=0.95,
                url=img,
                bounds=image_bounds,
            )
        )

        layer_classified = None
        if redis_instance.exists(f"{img_id}_classified") == 1:
            img_classified = pickle.loads(
                redis_instance.get(f"{img_id}_classified")
            )
            layer_classified = dl.LayerGroup(
                dl.ImageOverlay(
                    opacity=0.95,
                    url=img_classified,
                    bounds=image_bounds,
                )
            )

        return (
            layer_img,
            layer_classified,
            dash.no_update,
        )
    elif n_clicks and not selection:
        return (
            dash.no_update,
            dash.no_update,
            dmc.Notification(
                id="error-display",
                action="show",
                message="Please select an image from the table.",
            ),
        )
    return dash.no_update, dash.no_update, dash.no_update


# TODO: Finish and merge with bigger callback
@app.callback(
    Output("delete-div", "children"),
    Output("delete-notify", "children"),
    Input("delete", "n_clicks"),
    State("image-options", "selectedRows"),
)
def delete_img(n_clicks, selection):
    if n_clicks and selection:
        return selection, dash.no_update
    elif n_clicks and not selection:
        return dash.no_update, dmc.Notification(
            id="error-delete",
            action="show",
            message="Please select an image from the table.",
        )
    return dash.no_update, dash.no_update


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
def retrieve_data(n_clicks, date, lat, lon, dim):
    if n_clicks:
        msg = get_image(lat, lon, dim, date)
        df = update_df()
        return (
            dmc.Notification(id="update", action="show", message=msg),
            df.to_dict("records"),
            to_geojson(df),
        )
    return dash.no_update, dash.no_update, dash.no_update


@app.callback(
    Output("analyze-run-notify", "children"),
    Input("run-analysis", "n_clicks"),
    State("image-options", "selectedRows"),
    State("model-select", "value"),
    State("n-classes", "value"),
)
def run_analysis(n_clicks, selection, model, n_classes):
    if n_clicks and selection:
        img_id = selection[0]["id"]
        img = pickle.loads(redis_instance.get(img_id))
        image_array = process_img(img)
        if model == "k-means":
            segmentation = kmeans_cluster(image_array, n_classes)
            img_classified = create_colored_mask_image(segmentation, n_classes)
            img_info = pickle.loads(redis_instance.get(f"{img_id}_metadata"))
            img_info["classified"] = model
            redis_instance.set(f"{img_id}_metadata", pickle.dumps(img_info))
            redis_instance.set(
                f"{img_id}_classified", pickle.dumps(img_classified)
            )
            message = "Image classification successfully completed."
        else:
            message = (
                f"{model} not yet supported. Classification not completed."
            )

        return dmc.Notification(
            id="analysis-done", action="show", message=message
        )
    return dash.no_update


if __name__ == "__main__":
    app.run_server(debug=True)
