import dash
import dash_design_kit as ddk
from dash import dcc, html, Input, Output, State
import plotly.express as px
import dash_leaflet as dl
from datetime import date
import dash_mantine_components as dmc
import dash_ag_grid as dag
from dash_extensions.javascript import assign
from utils.data_utils import get_image
from constants import IMG_DIM


app = dash.Dash(__name__)
app.title = "Land cover analysis and classification"
server = app.server  # expose server variable for Procfile

df = px.data.stocks()

# How to render geojson.
point_to_layer = assign(
    """function(feature, latlng, context){
    const p = feature.properties;
    if(p.type === 'circlemarker'){return L.circleMarker(latlng, radius=p._radius)}
    if(p.type === 'circle'){return L.circle(latlng, radius=p._mRadius)}
    return L.marker(latlng);
}"""
)

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
                                min=0,
                                max=100,
                                step=10,
                                value=20,
                                marks=None,
                                tooltip={
                                    "placement": "bottom",
                                    "always_visible": True,
                                },
                            ),
                        ),
                        ddk.ControlItem(
                            label="Date",
                            children=dcc.DatePickerSingle(
                                id="my-date-picker",
                                min_date_allowed=date(1995, 8, 5),
                                max_date_allowed=date(2017, 9, 19),
                                date=date(2014, 2, 4),
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
                                    dl.GeoJSON(
                                        id="geojson",
                                        options=dict(
                                            pointToLayer=point_to_layer
                                        ),
                                        zoomToBounds=True,
                                    ),
                                    dl.LayersControl(
                                        dl.Overlay(
                                            name="Satellite image",
                                            checked=False,
                                            id="satellite-img",
                                        ),
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
                ddk.CardHeader(title="Select imagery to download"),
                ddk.Row(
                    [
                        dag.AgGrid(
                            id="image-options",
                            columnDefs=[
                                {"headerName": i, "field": i}
                                for i in df.columns
                            ],
                            rowData=df.to_dict("records"),
                            columnSize="sizeToFit",
                            defaultColDef=dict(
                                resizable=True,
                            ),
                        ),
                    ]
                ),
                dmc.Space(h=30),
                dmc.Center(html.Button("Download selections", id="download")),
            ],
            style={"height": "550px"},
        ),
    ]
)


# Get selected location data from the edit control to the geojson component.
@app.callback(
    Output("geojson", "data"),
    Input("edit_control", "geojson"),
    prevent_initial_call=True,
)
def loc_data(geojson):
    return geojson


@app.callback(
    Output("satellite-img", "children"),
    Input("get-data", "n_clicks"),
    State("my-date-picker", "date"),
    State("geojson", "data"),
    prevent_initial_call=True,
)
def loc_data(n_clicks, date, geojson):
    if n_clicks:
        print(geojson)
        lon, lat = geojson["features"][0]["geometry"]["coordinates"]
        image = get_image(lon, lat, date)
        image_bounds = [
            [(lat - (IMG_DIM / 2)), (lon - ((IMG_DIM / 2)))],
            [(lat + (IMG_DIM / 2)), (lon + ((IMG_DIM / 2)))],
        ]
        if image != None:
            img_overlay = (
                dl.LayerGroup(
                    dl.ImageOverlay(
                        opacity=0.95,
                        url=image,
                        bounds=image_bounds,
                    )
                ),
            )
            return img_overlay
        else:
            return dcc.Markdown(
                "Image is not available for the specified date or location."
            )
    else:
        return dash.no_update


@app.callback(
    Output("image-options", "rowData"), Input("get-data", "n_clicks")
)
def get_download_options(nclicks):
    if nclicks:
        print("get data!")
    return dash.no_update


if __name__ == "__main__":
    app.run_server(debug=True)
