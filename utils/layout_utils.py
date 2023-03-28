import dash
import dash_mantine_components as dmc
import dash_design_kit as ddk
from dash import dcc, html
import dash_leaflet as dl
import dash_ag_grid as dag
from datetime import date
from utils.chart_utils import create_class_distribution_pie_chart
from utils.data_utils import to_geojson, update_df
from dash_extensions import BeforeAfter
from constants import (
    BUTTON_STYLE,
    COLUMN_DEFS,
    MAP_HEIGHT,
    GRID_HEIGHT,
    PANEL_HEIGHT,
)


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
    layout = dmc.Center(
        html.Div(
            [
                dmc.Text("Proportion of land cover classes across study area"),
                dmc.Space(h=20),
                dcc.Graph(figure=pie),
            ]
        )
    )
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
                    "z-index": "1",
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
                children=dcc.DatePickerSingle(
                    id="my-date-picker",
                    min_date_allowed=date(2015, 8, 5),
                    max_date_allowed=date(2021, 9, 19),
                    date=date(2020, 8, 5),
                ),
                style={
                    "z-index": "2",
                },
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


def layout():
    df = update_df()
    layout = [
        ddk.Row(
            children=[
                download_controls(),
                leaflet_map(df),
            ]
        ),
        ddk.Card(
            children=[
                ddk.CardHeader(title="Select imagery to view"),
                ddk.Row(
                    [
                        image_table(df),
                        button_toolkit(),
                    ]
                ),
            ],
            style={"height": PANEL_HEIGHT},
        ),
        html.Div(children=notify_divs()),
        dmc.Modal(
            title=dmc.Text("Configure Image Analysis", weight=700),
            id="analyze-modal",
            size="40%",
            zIndex=10000,
            overlayOpacity=0.3,
        ),
        dmc.Modal(
            title=dmc.Text("Image details", weight=700),
            children=details_modal([1, 2, 3]),
            id="details-modal",
            size="40%",
            zIndex=10000,
            overlayOpacity=0.3,
        ),
    ]
    return layout


def use_cases_modal():
    return dmc.Modal(
    title=dmc.Text("Use cases", weight=700),
    children=dmc.Tabs(
        [
            dmc.TabsList(
                [
                    dmc.Tab("Water level", value="water-levels"),
                    dmc.Tab("Agriculture", value="agriculture"),
                    dmc.Tab("Construction", value="construction"),
                    dmc.Tab("Floods", value="floods"),
                ]
            ),
            dmc.TabsPanel(
                BeforeAfter(
                    before=dash.get_asset_url(
                        "before-after/shasta_lake_2019_july_13.jpg"
                    ),
                    after=dash.get_asset_url(
                        "before-after/shasta_lake_2021_june_16.jpg"
                    ),
                    width=512,
                    height=512,
                ),
                value="water-levels",
            ),
            dmc.TabsPanel(
                BeforeAfter(
                    before=dash.get_asset_url("before-after/crops_before.png"),
                    after=dash.get_asset_url("before-after/crops_after.png"),
                    width=512,
                    height=512,
                ),
                value="agriculture",
            ),
            dmc.TabsPanel(
                BeforeAfter(
                    before=dash.get_asset_url(
                        "before-after/construction_before.png"
                    ),
                    after=dash.get_asset_url(
                        "before-after/construction_after.png"
                    ),
                    width=512,
                    height=512,
                ),
                value="construction",
            ),
            dmc.TabsPanel(
                BeforeAfter(
                    before=dash.get_asset_url("before-after/flood_before.png"),
                    after=dash.get_asset_url("before-after/flood_after.png"),
                    width=512,
                    height=512,
                ),
                value="floods",
            ),
        ],
        color="red",
        orientation="vertical",
        value="water-levels",
    ),
    id="use-cases-modal",
    size="40%",
    zIndex=10000,
    overlayOpacity=0.3,
)
