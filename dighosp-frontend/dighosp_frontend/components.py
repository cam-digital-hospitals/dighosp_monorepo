"""Composite components for the digital twins app."""

from typing import Sequence

import dash_bootstrap_components as dbc
from dash import dcc, html
from dash_compose import composition


@composition
def simple_link_card(href: str, title: str, text: str, **kwargs):
    """A simple dbc.Card with a title (name) and main text (description),
    functioning as a hyperlink."""
    disabled = kwargs.pop('disabled', False)
    with dbc.Card(style={'height': '100%', 'width': '300px'}, **kwargs) as card:
        with dbc.CardBody():
            with html.H4(className="card-title"):
                yield title
            with html.P(className="card-text"):
                yield text
    if disabled:
        return card
    return dcc.Link(card, href=href)


def breadcrumb(labels: Sequence[str], paths: Sequence[str]):
    """A navigation breadcrumb, e.g. 'Home / Simulation / Job #foobar'.
    
    Args:
        label:
            The sequence of labels in the breadcrumb.
        paths:
            The path fragments forming the URL of the active page, e.g. ['des', 'foobar']
            for the path '/des/foobar'.
    """
    def crumb(label, href):
        return {
            'label': label,
            'href': href
        }

    def crumbs(labels, paths):
        urls = list('/' + s for s in map('/'.join, list(paths[:n] for n in range(len(paths)+1))))
        x = [crumb(*args) for args in list(zip(labels, urls))]
        del x[-1]['href']
        x[-1]['active'] = True
        return x
    return dbc.Breadcrumb(
        items=crumbs(labels, paths)
    )
