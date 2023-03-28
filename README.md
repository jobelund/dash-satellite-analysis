# Demo geospatial Dash app for satellite analysis

This Dash app was created to demo geospatial functionality for the March 2023 webinar. The app retrieves Landsat 8 data from a NASA API, caches the data in Redis, and allows the user to view the imagery and run basic classification models. 

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

Generate a NASA API key [here](https://api.nasa.gov/) and store as a `NASA` environment variable. This can be stored in a `.env` file for local development.

3. Run the following command:

```python
python app.py
```

> Note:

> 1. This command was adapted from the Procfile, which is the list of commands that are used when the application is deployed. The only difference is that `gunicorn` was replaced with `python` for running the application locally with Dash's devtools and reloading features.
