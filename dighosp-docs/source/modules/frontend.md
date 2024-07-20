# Frontend service

A frontend service is provided using Plotly [Dash](https://dash.plotly.com/). This simplifies development by maximising the using of Python throughout the codebase. Essentially, Dash is a Flask application &dash; you can easily deploy a Dash app using Flask's built-in server. However, this is heavily discouraged in the official Flask documentation:

```{warning}
Do not use the development server when deploying to production. It is intended for use only during local development. It is not designed to be particularly secure, stable, or efficient.
```

In the current Digital Hospitals platform architecture, we use `gunicorn` to host the Dash app:

```Dockerfile
# Dockerfile

CMD gunicorn dighosp_frontend.app:server -b "0.0.0.0:8000" -t ${TIMEOUT:-120} -w ${NUM_WORKERS:-4}
```

## Handling proxy prefixs

To handle hosting the frontend behind a prefix using Nginx, we define an environment variable DASH_BASE_PATHNAME:

```Dockerfile
# compose.override.yml

services:
  frontend:
    environment:
      DASH_BASE_PATHNAME: "/frontend/"
    # ports: !reset
```

This eventually gets stored as the Python variable `BASE_PATH`, which is fed into the Dash configuration options:

```py
# app.py

app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY],
                use_pages=True, suppress_callback_exceptions=True,
                assets_folder=conf.ASSETS_DIRNAME,
                routes_pathname_prefix=conf.BASE_PATH,    # Note these
                requests_pathname_prefix=conf.BASE_PATH)  # two lines
server = app.server
```

Finally, since we are handling prefixes in the Dash app, we instruct Nginx not to strip the prefix for us:

```nginx
# default.conf

location /frontend/ {
  proxy_pass http://frontend:8000;  # no trailing / = do not strip prefix
  proxy_read_timeout 180s;  # support longer Dash callbacks
  proxy_send_timeout 180s;  # support longer Dash callbacks
}
```

## Long callbacks

Due to the nature of Nginx and Dash, long-running callbacks may timeout unless the default settings are changed. This is done in Nginx's `default.conf` file as shown in the previous section.

Another option is to set up [background callbacks](https://dash.plotly.com/background-callbacks) in Dash, but this requires more effort. However, this would allow us to display loading messages and/or status updates for the callback.

## Assets folder

The `assets/` folder contains files that can be served to the client using `dash.get_asset_url()`. It also contains `.css` and `.js` files that are automatically served to the client, for custom styling and client-side functionality.

In particular, the `dashAgGridComponentFunctions.js` file is used for custom rending in AG Grid elements. For example, in the example below, we turn float values into datetime strings and string values into hyperlinks:

![screenshot](/_static/dash_ag_grid_des.png)