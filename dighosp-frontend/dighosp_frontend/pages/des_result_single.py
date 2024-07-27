"""DES module: Results page"""

from itertools import chain
from math import ceil

import dash
import dash_bootstrap_components as dbc
import numpy as np
import orjson
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from dash import Input, Output, callback, dcc, html
from dash_compose import composition

from dighosp_frontend.components import breadcrumb
from dighosp_frontend.conf import DES_FASTAPI_URL

# job_id: ObjectId of the simulation job
dash.register_page(__name__, path_template='/des/result/<job_id>')


@composition
def layout(job_id: str):
    """Page layout"""
    with html.Div() as ret:
        yield breadcrumb(
            labels=['🏠 Home', 'Process Simulation', f'Job {job_id}'],
            paths=['des', f'{job_id}']
        )
        yield html.H1("Digital Hospitals demo \u2014 Process Simulation")
        yield html.P(f"Job {job_id}")
        with html.Div(id='div-des-result-single'):
            with dbc.Card():
                with dbc.CardBody():
                    yield "Loading..."
        yield dcc.Store(id='store-des-job-id', data=job_id)
    return ret


@callback(
    Output('div-des-result-single', 'children'),
    Input('store-des-job-id', 'data')
)
@composition
def populate_card(job_id: str):
    """Generate the Card layout showing KPIs for the simulation job."""
    kpi_objs = get_kpi_objs(job_id)

    with dbc.Card(class_name='mb-3') as ret1:
        with dbc.CardBody():
            yield html.H3('Lab Turnaround Times')
            yield dbc.Table.from_dataframe(
                pd.DataFrame(kpi_objs['tat_table']),
                striped=True, bordered=True, hover=True
            )
            yield dcc.Graph(figure=kpi_objs['tat'])

    with dbc.Card(class_name='mb-3') as ret2:
        with dbc.CardBody():
            yield html.H3('Work in Progress')
            yield dcc.Graph(figure=kpi_objs['wip'])
            n = get_num_reps(job_id)
            yield html.P(f"""\
Bands denote the lower and upper deciles (light blue) and quantiles (dark blue); the black line \
denotes the median ({n} simulation runs).""")

    with dbc.Card(class_name='mb-3') as ret3:
        with dbc.CardBody():
            yield html.H3('Resource Utilisation')
            yield dbc.Table.from_dataframe(
                pd.DataFrame(kpi_objs['utilisation_table']),
                striped=True, bordered=True, hover=True
            )
            yield dcc.Graph(figure=kpi_objs['utilisation'])

    return [ret1, ret2, ret3]


def get_num_reps(job_id: str) -> dict:
    """Get the KPI-related figure objects for a given job."""
    url = f'{DES_FASTAPI_URL}/jobs/{job_id}/status'
    response = requests.get(url, timeout=100)
    if response.status_code != 200:  # OK
        raise Exception(f'HTTP code {response.status_code} from backend server')
    data = orjson.loads(response.text)
    return data['max_progress']



def get_kpi_objs(job_id: str) -> dict:
    """Get the KPI-related figure objects for a given job."""
    url = f'{DES_FASTAPI_URL}/jobs/{job_id}/results/dash_objs'
    response = requests.get(url, timeout=100)
    if response.status_code != 200:  # OK
        raise Exception(f'HTTP code {response.status_code} from backend server')
    return orjson.loads(response.text)
