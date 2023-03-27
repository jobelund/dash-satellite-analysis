import requests, PIL, io, json, pickle, cv2
from constants import redis_instance, REDIS_EXPIRE_SEC, NASA_KEY
import pandas as pd
import dash_leaflet.express as dlx
from sklearn import cluster
import numpy as np
from PIL import Image
import plotly.express as px


def get_image(lat, lon, dim, name, date="2014-02-04"):
    img_url = f"https://api.nasa.gov/planetary/earth/imagery?lon={lon}&lat={lat}&date={date}&dim={dim}&api_key={NASA_KEY}"
    asset_url = f"https://api.nasa.gov/planetary/earth/assets?lon={lon}&lat={lat}&date={date}&dim={dim}&api_key={NASA_KEY}"
    img_metadata = json.loads(requests.get(asset_url).content)

    if any(key in img_metadata for key in ["msg", "error"]):
        msg = img_metadata["msg"]
        print(asset_url)
        return f"Error retrieving data: {msg}"
    elif "id" in img_metadata.keys():
        img_id = img_metadata["id"]
        if img_id in [x.decode("utf8") for x in redis_instance.keys()]:
            img = pickle.loads(redis_instance.get(img_id))
            return "Image already stored in redis. Loading from cache."
        else:
            print("Retrieving image data from API...")
            img_data = requests.get(img_url).content
            image_bytes = io.BytesIO(img_data)
            img = PIL.Image.open(image_bytes)
            img = enhance_image(img)
            img_info = {
                "name": name,
                "lat": lat,
                "lon": lon,
                "dim": dim,
                "date": date,
                "id": img_id,
            }

            redis_instance.set(img_id, pickle.dumps(img))
            redis_instance.set(f"{img_id}_metadata", pickle.dumps(img_info))
            redis_instance.expire(img_id, REDIS_EXPIRE_SEC)
            redis_instance.expire(f"{img_id}_metadata", REDIS_EXPIRE_SEC)
            return f"{img_id} successfully retrieved and stored in database."


def update_df(df=None):
    df = (
        pd.DataFrame(
            columns=[
                "name",
                "id",
                "date",
                "lat",
                "lon",
                "dim",
                "classified",
                "n classes",
                "class distribution",
            ]
        )
        if not df
        else df
    )
    for key in redis_instance.keys("*_metadata"):
        df = df.append(
            pickle.loads(redis_instance.get(key)), ignore_index=True
        )
    return df


def to_geojson(df):
    return dlx.dicts_to_geojson(
        df.rename(columns={"name": "tooltip"}).to_dict("records")
    )


def kmeans_cluster(img_array, n_clusters):
    """
    Performs k-means clustering on a single-band image.

    Args:
        img_array (np.ndarray): A 2D NumPy array representing the input single-band image.
        n_clusters (int): The number of clusters to use for the k-means algorithm.

    Returns:
        np.ndarray: A 2D NumPy array representing the clustering labels of the input image.

    """
    img = img_array[:, :, 0]  # Just get one band of the image
    X = img.reshape((-1, 1))
    k_means = cluster.KMeans(n_clusters=n_clusters)
    k_means.fit(X)
    segmentation = k_means.labels_
    segmentation = segmentation.reshape(img.shape)

    return segmentation


def calculate_class_proportions(segmentation, n_clusters):
    """
    Calculates the proportion of pixels in each cluster in a clustering label image.

    Args:
        segmentation (np.ndarray): A 2D NumPy array representing the clustering labels of an image.
        n_clusters (int): The number of clusters used to generate the clustering label image.

    Returns:
        np.ndarray: A 1D NumPy array representing the proportion of pixels in each cluster.

    """
    total_pixels = segmentation.size
    class_counts = np.zeros(n_clusters, dtype=int)

    for i in range(n_clusters):
        class_counts[i] = np.sum(segmentation == i)

    class_proportions = class_counts / total_pixels
    return np.round(class_proportions, 3)


def create_colored_mask_image(segmentation, n_clusters):
    """
    Creates a color mask image from a segmentation label image.

    Args:
        segmentation (np.ndarray): A 2D NumPy array representing the segmentation label image.
        n_clusters (int): The number of clusters used to generate the segmentation label image.

    Returns:
        PIL.Image.Image: A new PIL Image object representing the color mask image.

    """
    # Use the colors from the Plotly Viridis colorscale
    colorscale = px.colors.sequential.Viridis

    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    rgb_colorscale = [hex_to_rgb(color) for color in colorscale]

    # Interpolate the colorscale to have n_clusters colors
    interpolated_colors = []
    for i in range(n_clusters):
        position = i / (n_clusters - 1) * (len(colorscale) - 1)
        lower_color = rgb_colorscale[int(position)]
        upper_color = rgb_colorscale[
            min(int(position) + 1, len(colorscale) - 1)
        ]
        ratio = position % 1
        interpolated_color = tuple(
            [
                int(lower_color[i] * (1 - ratio) + upper_color[i] * ratio)
                for i in range(3)
            ]
        )
        interpolated_colors.append(interpolated_color)

    colored_mask = np.zeros(
        (segmentation.shape[0], segmentation.shape[1], 3), dtype=np.uint8
    )

    class_colors = []
    for i, color in enumerate(interpolated_colors):
        colored_mask[segmentation == i] = color
        class_colors.append(color)

    return Image.fromarray(colored_mask), class_colors


def process_img(image, resize=(256, 256)):
    """
    Preprocesses a PIL image for use in a machine learning model.

    Args:
        image (PIL.Image.Image): The input image to preprocess.
        resize (tuple[int, int]): The target size of the image after resizing. Defaults to (256, 256).

    Returns:
        np.ndarray: A 3D NumPy array representing the preprocessed image, with pixel values normalized to [0, 1].

    """
    image = image.resize(resize)
    # Convert the image to a numpy array and normalize its values
    img_array = np.array(image).astype(np.float32) / 255
    return img_array


def enhance_image(image, clip_limit=3.1):
    """
    Enhances the contrast of a PIL image using the CLAHE algorithm.

    Args:
        image (PIL.Image.Image): The input RGB image to enhance.
        clip_limit (float, optional): The CLAHE clip limit. Defaults to 3.1.

    Returns:
        PIL.Image.Image: A new PIL image with enhanced contrast.

    """
    img_array = np.array(image)

    # Convert to LAB color space
    lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)

    # Split into channels
    l, a, b = cv2.split(lab)

    # Apply histogram equalization to the L channel
    clahe = cv2.createCLAHE(clip_limit, tileGridSize=(10, 10))
    cl = clahe.apply(l)

    # Merge the channels back into the LAB image
    lab = cv2.merge((cl, a, b))

    # Convert back to RGB color space
    enhanced_image = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
    return Image.fromarray(enhanced_image)
