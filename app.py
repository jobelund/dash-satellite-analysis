import dash
import dash_design_kit as ddk
from dash import dcc, html, Input, Output, State
import dash_leaflet as dl
import dash_mantine_components as dmc
import warnings
import pickle

from constants import redis_instance
from utils.layout_utils import (
    analysis_modal,
    details_modal,
    notify_divs,
    button_toolkit,
    leaflet_map,
    image_table,
    download_controls,
)
from utils.data_utils import (
    update_df,
    get_image,
    to_geojson,
    kmeans_cluster,
    calculate_class_proportions,
    create_colored_mask_image,
    process_img,
)

# Temporary -- muting pandas warnings for using df.append()
warnings.simplefilter(action="ignore", category=FutureWarning)

app = dash.Dash(__name__, prevent_initial_callbacks="initial_duplicate")
app.title = "Land cover analysis and classification"
server = app.server  # expose server variable for Procfile

df = update_df()

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
                style={"height": "300px"},
            ),
            html.Div(children=notify_divs()),
            dmc.Modal(
                title="Configure Image Analysis",
                id="analyze-modal",
                size="40%",
                zIndex=10000,
                overlayOpacity=0.3,
            ),
            dmc.Modal(
                title="Image details",
                id="details-modal",
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
    Output("analyze-modal", "opened", allow_duplicate=True),
    Output("analyze-modal", "children", allow_duplicate=True),
    Output("analyze-notify", "children"),
    Input("classify", "n_clicks"),
    State("analyze-modal", "opened"),
    State("image-options", "selectedRows"),
    prevent_initial_call=True,
)
def modal_classify(n_clicks, opened, selected):
    if n_clicks and selected:
        return not opened, analysis_modal(), dash.no_update
    if n_clicks and not selected:
        return (
            dash.no_update,
            dash.no_update,
            dmc.Notification(
                id="classify-notfication",
                action="show",
                message="Can't classify. Please select an image from the table.",
            ),
        )
    return dash.no_update, dash.no_update, dash.no_update


@app.callback(
    Output("details-modal", "opened"),
    Output("details-modal", "children"),
    Output("investigate-notify", "children"),
    Input("investigate", "n_clicks"),
    State("details-modal", "opened"),
    State("image-options", "selectedRows"),
    prevent_initial_call=True,
)
def modal_details(n_clicks, opened, selected):
    if n_clicks and selected:
        img_id = selected[0]["id"]
        if redis_instance.exists(f"{img_id}_classified") == 1:
            class_proportions = selected[0]["class distribution"]
            return not opened, details_modal(class_proportions), dash.no_update
        else:
            return (
                dash.no_update,
                dash.no_update,
                dmc.Notification(
                    id="investigate-notfication",
                    action="show",
                    message="Can't investigate. Please classify image.",
                ),
            )

    elif n_clicks and not selected:
        return (
            dash.no_update,
            dash.no_update,
            dmc.Notification(
                id="investigate-notfication",
                action="show",
                message="Can't investigate. Please select an image from the table.",
            ),
        )
    return dash.no_update, dash.no_update, dash.no_update


# TODO: Somewhat buggy - maybe have display always on when a row is selected?
@app.callback(
    Output("satellite-img", "children"),
    Output("classified-img", "children"),
    Output("display-notify", "children"),
    Input("display", "n_clicks"),
    State("image-options", "selectedRows"),
)
def img_display(n_clicks, selection):
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
                id="display-notfication",
                action="show",
                message="Can't display. Please select an image from the table.",
            ),
        )
    return dash.no_update, dash.no_update, dash.no_update


# TODO: Delete image from map as well!
@app.callback(
    Output("image-options", "rowData", allow_duplicate=True),
    Output("geojson", "data", allow_duplicate=True),
    Output("delete-notify", "children"),
    Input("delete", "n_clicks"),
    State("image-options", "selectedRows"),
    prevent_initial_callback=True,
)
def img_delete(n_clicks, selection):
    if n_clicks and selection:
        img_id = selection[0]["id"]
        for key in [img_id, f"{img_id}_metadata", f"{img_id}_classified"]:
            if redis_instance.exists(key) == 1:
                redis_instance.delete(key)
        df = update_df()
        return (
            df.to_dict("records"),
            to_geojson(df),
            dmc.Notification(
                id="delete-notfication",
                action="show",
                message=f"{img_id} successfully deleted.",
            ),
        )
    elif n_clicks and not selection:
        return (
            dash.no_update,
            dash.no_update,
            dmc.Notification(
                id="delete-notfication",
                action="show",
                message="Can't delete. Please select an image from the table.",
            ),
        )
    return dash.no_update, dash.no_update, dash.no_update


@app.callback(
    Output("analyze-run-notify", "children"),
    Output("analyze-modal", "opened", allow_duplicate=True),
    Output("image-options", "rowData", allow_duplicate=True),
    Input("run-analysis", "n_clicks"),
    State("image-options", "selectedRows"),
    State("model-select", "value"),
    State("n-classes", "value"),
    State("analyze-modal", "opened"),
    prevent_initial_call=True,
)
def img_classify(n_clicks, selection, model, n_classes, opened):
    if n_clicks and selection:
        img_id = selection[0]["id"]
        img = pickle.loads(redis_instance.get(img_id))
        image_array = process_img(img)
        if model == "k-means":
            segmentation = kmeans_cluster(image_array, n_classes)
            class_proportions = calculate_class_proportions(
                segmentation, n_classes
            )
            img_classified = create_colored_mask_image(segmentation, n_classes)
            img_info = pickle.loads(redis_instance.get(f"{img_id}_metadata"))
            img_info["classified"] = model
            img_info["n classes"] = n_classes
            img_info["class distribution"] = class_proportions
            redis_instance.set(f"{img_id}_metadata", pickle.dumps(img_info))
            redis_instance.set(
                f"{img_id}_classified", pickle.dumps(img_classified)
            )
            message = "Image classification successfully completed."
        else:
            message = (
                f"{model} not yet supported. Classification not completed."
            )

        return (
            dmc.Notification(
                id="analysis-done", action="show", message=message
            ),
            not opened,
            update_df().to_dict("records"),
        )
    return dash.no_update, dash.no_update, dash.no_update


@app.callback(
    Output("map-view", "center"),
    Output("map-view", "zoom"),
    Input("image-options", "selectedRows"),
)
def map_zoom(selection):
    if selection:
        return (float(selection[0]["lat"]), float(selection[0]["lon"])), 12
    return dash.no_update


@app.callback(
    Output("data-notify", "children"),
    Output("image-options", "rowData", allow_duplicate=True),
    Output("geojson", "data", allow_duplicate=True),
    Input("get-data", "n_clicks"),
    State("my-date-picker", "value"),
    State("lat", "value"),
    State("lon", "value"),
    State("img-dim", "value"),
    State("name", "value"),
    prevent_initial_call=True,
)
def data_retrieve(n_clicks, date, lat, lon, dim, name):
    if n_clicks:
        msg = get_image(lat, lon, dim, name, date)
        df = update_df()
        return (
            dmc.Notification(id="update", action="show", message=msg),
            df.to_dict("records"),
            to_geojson(df),
        )
    return dash.no_update, dash.no_update, dash.no_update


if __name__ == "__main__":
    app.run_server(debug=True)
