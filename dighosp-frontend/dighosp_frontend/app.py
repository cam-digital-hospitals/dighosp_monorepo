"""Main module for the front-end."""

from pathlib import Path

import dash
import dash_bootstrap_components as dbc
from dash import html
from dash_compose import composition

from dighosp_frontend import conf

app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY],
                use_pages=True, suppress_callback_exceptions=True,
                assets_folder=conf.ASSETS_DIRNAME)


@composition
def app_main():
    """Layout for the overall app."""
    with html.Div(
        className='mx-5',
        style={'max-width': '1600px'}
    ) as ret:
        with dbc.NavbarSimple(
            brand='Digital Hospitals Demo',
            brand_href='/#',
            color='primary',
            dark=True,
            fluid=True
        ):
            with dbc.NavItem():
                with dbc.NavLink(href='/#'):
                    yield "Home"
        yield dash.page_container
    return ret


app.layout = app_main()

if __name__ == "__main__":
    app.run_server(debug=True)
