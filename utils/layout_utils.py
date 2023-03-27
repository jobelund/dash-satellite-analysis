import dash_mantine_components as dmc
import dash_design_kit as ddk
from dash import dcc, html
from utils.chart_utils import create_class_distribution_pie_chart


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


def details_modal(class_proportions):
    pie = create_class_distribution_pie_chart(class_proportions)
    layout = dmc.Center(
        html.Div(
            dcc.Graph(figure=pie, style={"height": "200px", "width": "200px"})
        )
    )
    return layout
