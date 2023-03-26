import dash_mantine_components as dmc
import dash_design_kit as ddk
from dash import dcc, html


def analysis_modal():
    data = [["k-means", "K-Means"], ["random-forest", "Random Forest"]]
    layout = dmc.Center(
        html.Div(
            [
                dmc.RadioGroup(
                    [dmc.Radio(l, value=k) for k, l in data],
                    id="radiogroup-simple",
                    value="react",
                    label="Select a classification model",
                    size="sm",
                    mt=10,
                ),
                dmc.Space(h=30),
                dmc.NumberInput(
                    label="Number of classes",
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
