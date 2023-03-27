import dash_mantine_components as dmc
import dash_design_kit as ddk
from dash import dcc, html
import dash_leaflet as dl
import dash_ag_grid as dag
from datetime import date
from utils.chart_utils import create_class_distribution_pie_chart
from utils.data_utils import to_geojson
from constants import BUTTON_STYLE, COLUMN_DEFS, MAP_HEIGHT, GRID_HEIGHT


def analysis_modal():
    data = [["k-means", "K-Means"], ["random-forest", "Random Forest"]]
    layout = dmc.Center(
        html.Div(
            [
                dmc.RadioGroup(
                    [dmc.Radio(l, value=k) for k, l in data],
                    id="model-select",
                    value="k-means",
                    label="Select a classification model",
                    size="sm",
                    mt=10,
                ),
                dmc.Space(h=30),
                dmc.NumberInput(
                    label="Number of classes",
                    id="n-classes",
                    value=5,
                    min=0,
                    step=1,
                    style={"width": 250},
                ),
                dmc.Space(h=30),
                dmc.Center(
                    dmc.Button("Run classification", id="run-analysis")
                ),
            ]
        )
    )
    return layout


def details_modal(class_proportions, class_colors=None):
    pie = create_class_distribution_pie_chart(class_proportions, class_colors)
    layout = dmc.Center(html.Div(dcc.Graph(figure=pie)))
    return layout


def notify_divs():
    items = [
        "data",
        "display",
        "analyze",
        "analyze-run",
        "investigate",
        "delete",
    ]
    return [html.Div(id=f"{item}-notify") for item in items]


def button_toolkit():
    button_types = ["display", "crop", "classify", "investigate", "delete"]
    buttons = [
        dmc.Center(html.Button(item.capitalize(), id=item, style=BUTTON_STYLE))
        for item in button_types
    ]
    return ddk.Block(width=20, children=buttons)


def leaflet_map(df):
    return ddk.Block(
        style={"margin": "10px"},
        width=80,
        children=html.Div(
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
                                children=dl.LayerGroup(id="satellite-img"),
                            ),
                            dl.Overlay(
                                name="Classified image",
                                checked=True,
                                children=dl.LayerGroup(id="classified-img"),
                            ),
                        ]
                    ),
                    dl.FeatureGroup([dl.EditControl(id="edit-control")]),
                ],
                style={
                    "width": "100%",
                    "height": MAP_HEIGHT,
                    "margin": "auto",
                    "display": "block",
                },
            )
        ),
    )


def image_table(df):
    return ddk.Block(
        width=85,
        children=[
            dmc.LoadingOverlay(
                dag.AgGrid(
                    id="image-options",
                    className="ag-theme-material",
                    columnDefs=COLUMN_DEFS,
                    rowData=df.to_dict("records"),
                    columnSize="sizeToFit",
                    defaultColDef={
                        "resizable": True,
                        "sortable": True,
                        "filter": True,
                    },
                    dashGridOptions={"rowSelection": "single"},
                    style={"height": GRID_HEIGHT, "margin": "10px"},
                )
            ),
        ],
    )


def download_controls():
    return ddk.ControlCard(
        width=20,
        children=[
            ddk.CardHeader(title="Data access"),
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
            ddk.ControlItem(
                label="Name",
                children=dcc.Input(
                    type="text", id="name", placeholder="Image name..."
                ),
            ),
            dmc.Center(
                html.Button(
                    "Download image", id="get-data", style=BUTTON_STYLE
                )
            ),
        ],
        style={"height": MAP_HEIGHT},
    )
