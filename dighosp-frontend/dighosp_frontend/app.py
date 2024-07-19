"""Main module for the front-end."""

import dash
import dash_bootstrap_components as dbc
from dash import html
from dash_compose import composition

from dighosp_frontend import conf

app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY],
                use_pages=True, suppress_callback_exceptions=True,
                assets_folder=conf.ASSETS_DIRNAME,
                routes_pathname_prefix=conf.BASE_PATH,
                requests_pathname_prefix=conf.BASE_PATH)
server = app.server


@composition
def app_main():
    """Layout for the overall app."""
    with html.Div(
        className='mx-5',
        style={'max-width': '1600px'}
    ) as ret:
        with dbc.NavbarSimple(
            brand='Digital Hospitals Demo',
            brand_href=dash.get_relative_path('/#'),
            color='primary',
            dark=True,
            fluid=True
        ):
            with dbc.NavItem():
                with dbc.NavLink(href=dash.get_relative_path('/#')):
                    yield "Home"
        yield dash.page_container
    return ret


app.layout = app_main()

# Runs in Debug mode if this file is run directly.
# In production, this is not executed.
if __name__ == "__main__":
    app.run(debug=True)
