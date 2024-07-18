"""Home page for the Digital Hospitals app."""

from pathlib import Path

import dash
import dash_bootstrap_components as dbc
import toml
from dash import dcc, html
from dash_compose import composition

from dighosp_frontend.components import breadcrumb, simple_link_card

dash.register_page(__name__, path='/')
LABELS = ['🏠 Home']
PATHS = []


@composition
def layout():
    """Page layout.

    Read a list of service definitions from services.toml and display a dbc.Card element for each.
    Each card is displayed as a clickable link unless "disabled = true" is present.
    """

    # parents: pages -> dighosp_frontend -> dighosp-frontend
    services_filename = Path(__file__).resolve().parents[2].joinpath('services.toml')

    with html.Div() as ret:
        yield breadcrumb(LABELS, PATHS)
        with dcc.Markdown():
            yield """\
# Digital Hospitals demo

**Authors: ** Digital Hospitals group, Institute for Manufacturing, University of Cambridge

This website provides a demonstrator for the Digital Hospitals platform for Addenbrooke's Hospital,
Cambridge, using the Histopathology laboratory as an initial case study.

## Modules
"""
        with dbc.Container(fluid=True):
            with dbc.Row():
                for card_data in toml.load(services_filename).values():
                    card_data: dict
                    with dbc.Col(width='auto', class_name='mb-3'):
                        yield simple_link_card(
                            href=card_data.pop('href'),
                            title=card_data.pop('name'),
                            text=card_data.pop('description'),
                            **card_data
                        )
    return ret
