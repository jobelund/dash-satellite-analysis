import plotly.graph_objects as go


def create_class_distribution_pie_chart(class_proportions, class_colors=None):
    """
    Creates a pie chart showing the distribution of pixels in each cluster.

    Args:
        class_proportions (np.ndarray): A 1D NumPy array representing the proportion of pixels in each cluster.

    Returns:
        plotly.graph_objs._figure.Figure: A new plotly pie chart figure showing the distribution of pixels in each cluster.

    """
    cluster_ids = list(range(len(class_proportions)))
    fig = go.Figure(
        go.Pie(
            labels=cluster_ids,
            values=class_proportions,
            textinfo="label+percent",
            insidetextorientation="radial",
            marker=dict(colors=class_colors),
        )
    )

    fig.update_layout(
        title="Class Distribution",
        width=600,
        height=400,
    )

    return fig
