# Satellite Flood Detection

This Dash app was created for Plotly.

## Development

Install development-specific requirements by running

```
pip install -r requirements-dev.txt
```

## Running this application

1. Install the Python dependencies

```
pip install -r requirements.txt --extra-index-url <your-dash-enterprise-packages-url>
```

2. Set up environment variables 

Data access via the [Copernicus Open Access Hub](https://scihub.copernicus.eu/dhus/#/home) requires login credentials which should be stored under `DHUS_USER` and `DHUS_PASSWORD` environment variables. These can be stored in a `.env` file for local development. 

3. Run the following command:

```python
python app.py
```

> Note:

> 1. This command was adapted from the Procfile, which is the list of commands that are used when the application is deployed. The only difference is that `gunicorn` was replaced with `python` for running the application locally with Dash's devtools and reloading features.




