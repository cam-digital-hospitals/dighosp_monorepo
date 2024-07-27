"""Main module for the front-end."""

from pathlib import Path
import dash
import dash_bootstrap_components as dbc
from dash import html
from dash_compose import composition

from dighosp_frontend import conf
import toml

app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY],
                use_pages=True, suppress_callback_exceptions=True,
                assets_folder=conf.ASSETS_DIRNAME,
                routes_pathname_prefix=conf.BASE_PATH,
                requests_pathname_prefix=conf.BASE_PATH)
server = app.server


@composition
def app_main():
    # parents: dighosp_frontend -> dighosp-frontend
    services_filename = Path(__file__).resolve().parents[1].joinpath('services.toml')
    
    """Layout for the overall app."""
    with html.Div(
        className='mx-5',
        style={'max-width': '1600px'}
    ) as ret:
        with dbc.NavbarSimple(
            brand=f'Digital Hospitals Demo v{conf.APP_VERSION.base_version}',
            brand_href=dash.get_relative_path('/#'),
            color='primary',
            dark=True,
            fluid=True
        ):
            with dbc.NavItem():
                with dbc.NavLink(href=dash.get_relative_path('/#')):
                    yield "Home"
            with dbc.DropdownMenu(nav=True, in_navbar=True, label='Modules'):
                for service_data in toml.load(services_filename).values():
                    if service_data.get('disabled', False):
                        continue
                    service_data: dict
                    yield dbc.DropdownMenuItem(
                        service_data['name'],
                        href=dash.get_relative_path(service_data['href'])
                    )
            with dbc.DropdownMenu(nav=True, in_navbar=True, label='Developer'):
                yield dbc.DropdownMenuItem(
                    "Docs", href='/docs', external_link=True, target='_blank')
                yield dbc.DropdownMenuItem(
                    "MongoDB admin", href='/mongoadmin', external_link=True, target='_blank')
        yield dash.page_container
    return ret


app.layout = app_main()

# Runs in Debug mode if this file is run directly.
# In production, this is not executed.
if __name__ == "__main__":
    app.run(debug=True)
