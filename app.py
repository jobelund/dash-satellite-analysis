import dash
import dash_design_kit as ddk
from dash import dcc, html, Input, Output
import plotly.express as px
import dash_leaflet as dl
from datetime import date
import dash_mantine_components as dmc
import dash_ag_grid as dag

app = dash.Dash(__name__)
app.title = "Land cover analysis and classification"
server = app.server  # expose server variable for Procfile

df = px.data.stocks()

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
                            label="Maximum cloud cover percentage",
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
                            label="Date range",
                            children=dcc.DatePickerRange(
                                id="my-date-picker-range",
                                min_date_allowed=date(1995, 8, 5),
                                max_date_allowed=date(2017, 9, 19),
                                start_date=date(2017, 5, 5),
                                end_date=date(2017, 8, 25),
                            ),
                        ),
                        ddk.ControlItem(
                            label="Product type",
                            children=dcc.RadioItems(
                                ["Level-1B", "Level-1C", "Level-2A"],
                                "Level-2A",
                                inline=True,
                            ),
                        ),
                        dmc.Space(h=50),
                        html.Button("Retrieve image options", id="get-data"),
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
                                    dl.GeoJSON(data="assets/bangladesh.json"),
                                    dl.LayersControl(),
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


# Copy data from the edit control to the geojson component.
# @app.callback(Output("geojson", "data"), Input("edit_control", "geojson"))
# def mirror(x):
#     if not x:
#         raise PreventUpdate
#     return x


@app.callback(
    Output("image-options", "rowData"), Input("get-data", "n_clicks")
)
def get_download_options(nclicks):
    if nclicks:
        print("get data!")
    return dash.no_update


if __name__ == "__main__":
    app.run_server(debug=True)
