import plotly.express as px
import dash_design_kit as ddk


def generate_splom(df):
    splom = px.scatter_matrix(
        df,
        dimensions=[
            "sepal_width",
            "sepal_length",
            "petal_width",
            "petal_length",
        ],
    )
    return splom


def generate_scatter(df):
    scatter = px.scatter(
        df,
        x="sepal_width",
        y="sepal_length",
        marginal_y="violin",
        marginal_x="violin",
    )
    return scatter


def generate_density(df):
    density = px.density_contour(df, x="sepal_width", y="sepal_length")
    return density


def generate_table(df):
    df = df.head(25)
    table = ddk.DataTable(
        data=df.to_dict("records"),
        columns=[{"name": i, "id": i} for i in df.columns],
        page_action="none",
    )
    return table
