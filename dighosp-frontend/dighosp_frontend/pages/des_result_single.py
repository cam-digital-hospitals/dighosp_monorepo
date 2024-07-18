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
            labels=['🏠 Home', 'Process sim', f'Job {job_id}'],
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
    n = n_results(job_id)
    # TODO: error handling
    # TODO: fix speed issue
    data = [get_result_single(job_id, idx) for idx in range(n)]

    with dbc.Card(class_name='mb-3') as ret1:
        with dbc.CardBody():
            yield dcc.Graph(figure=utilisation_fig(data))

    with dbc.Card(class_name='mb-3') as ret2:
        with dbc.CardBody():
            yield dcc.Graph(figure=wips_fig(data, 'Total WIP'))
            yield html.P(f"""\
Bands denote the lower and upper deciles (light blue) and quantiles (dark blue); the black line \
denotes the median ({n} simulation runs).""")

    with dbc.Card(class_name='mb-3') as ret3:
        with dbc.CardBody():
            yield dcc.Graph(figure=lab_tats_fig(data))

    return [ret1, ret2, ret3]


def n_results(job_id: str) -> int:
    """Get the number of results for a simulation job."""
    url = f'{DES_FASTAPI_URL}/jobs/{job_id}/status'
    response = requests.get(url, timeout=100)
    if response.status_code != 200:  # OK
        raise Exception(f'HTTP code {response.status_code} from backend server')
    return response.json()['max_progress']


def get_result_single(job_id: str, idx: int) -> dict:
    """Get a single simulation result."""
    # Catch these exceptions in order:
    #    requests.ConnectionError
    #    requests.Timeout
    #    requests.RequestException
    #    Exception
    url = f'{DES_FASTAPI_URL}/jobs/{job_id}/results/{idx}'
    print(url)
    response = requests.get(url, timeout=100)
    if response.status_code != 200:  # OK
        raise Exception(f'HTTP code {response.status_code} from backend server')
    return orjson.loads(response.text)


def timeseries_mean(df: pd.DataFrame, time_col: str = 't', val_col: str = 'x'):
    """Get the time-weighted mean of a pandas Series."""
    _tmp = df.copy()
    # diff() starts with 'NaN' in first row, so shift(-1) is needed
    return float(np.average(_tmp[val_col][:-1], weights=_tmp[time_col].diff().shift(-1)[:-1]))


def mean_claimed(data: dict, resource_name: str):
    """Get the mean number of busy units of a resource, for a single simulation replication."""
    df = pd.DataFrame(
        data['resources']['n_claimed'][resource_name],
        columns=['t', 'x']
    )
    return timeseries_mean(df)


def mean_available(data: dict, resource_name: str):
    """Get the mean number of available units of a resource, for a single simulation replication."""
    df = pd.DataFrame(
        data['resources']['capacity'][resource_name],
        columns=['t', 'x']
    )
    return timeseries_mean(df)


def utilisation_medians(data):
    """Get the mean utilisation of each resource in the model, taking the median of the
    simulation replications."""
    return {
        res: {
            'median': np.median([mean_claimed(dd, res)/mean_available(dd, res) for dd in data])
        }
        for res in data[0]['resources']['n_claimed'].keys()
    }


def utilisation_fig(data):
    """Create boxplots for the mean utilisation of each resource in the model (across
    multiple simulation replications), sorted by decreasing order of the median."""
    df = pd.DataFrame.from_dict(
        utilisation_medians(data), orient='index').sort_values(by='median', ascending=False)
    df2 = pd.concat([
        pd.DataFrame([[res, mean_claimed(dd, res)/mean_available(dd, res)] for dd in data],
                     columns=['label', 'value'])
        for res in data[0]['resources']['n_claimed'].keys()
    ])
    fig = px.box(df2, 'label', 'value')
    fig.update_xaxes(categoryorder='array', categoryarray=df.index, title='Resource')
    fig.update_yaxes(title='Mean utilisation')
    fig.update_layout(title='Resource utilisation')
    return fig


def wip_df(data, wip):
    """Get the hourly means for a given WIP counter, for a single simulation replication."""
    df = pd.DataFrame(data['wips'][wip], columns=['t', 'x']).set_index('t')
    df.index = pd.to_timedelta(df.index, unit='h')
    df = df.resample('h').mean().ffill()
    return df


def wips_df(data, wip):
    """Get the quantiles of the hourly means for a given WIP counter, across all simulation
    replications."""
    df = pd.concat([wip_df(dd, wip) for dd in data], axis=1)
    df2 = pd.DataFrame({
        'q10': df.quantile(0.1, axis=1),
        'q25': df.quantile(0.25, axis=1),
        'median': df.quantile(0.5, axis=1),
        'q75': df.quantile(0.75, axis=1),
        'q90': df.quantile(0.9, axis=1)
    })
    df2.index = df2.index / pd.Timedelta(days=1)
    return df2


def wips_fig(data, wip):
    """Plot the quantiles of the hourly means for a given WIP counter, across all simulation
    replications."""
    df = wips_df(data, wip)
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df.index, y=df.q90,
        line_width=0, line_color='rgba(255,255,255,0)',
        name='90th percentile'
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=df.q10,
        fill='tonexty', fillcolor='rgba(0,0,255,0.2)', mode='none',
        name='10th percentile'
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=df.q75,
        line_width=0, line_color='rgba(255,255,255,0)',
        name='75th percentile'
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=df.q25,
        fill='tonexty', fillcolor='rgba(0,0,255,0.4)', mode='none',
        name='25th percentile'
    ))
    fig.add_trace(go.Scatter(
        x=df.index, y=df['median'],
        line_color='rgb(0,0,0)',
        name='median'
    ))

    fig.update_layout(showlegend=False, title='Total WIP, hourly means')
    fig.update_xaxes(title='Days')
    fig.update_yaxes(title='Work in progress')
    return fig


def lab_tats_fig(data):
    """Plot a histogram of lab turnaround times, using all simulation replications as data."""
    lab_tats = [[
        (x['qc_end']-x['reception_start'])/24.0
        for x in data[n]['specimen_data'].values()
        if 'reporting_end' in x
    ] for n in range(len(data))]
    lab_tats = list(chain(*lab_tats))
    df = pd.DataFrame(lab_tats, columns=['x'])
    fig = px.histogram(df, x='x', nbins=28, histnorm='probability')
    fig.update_traces(
        xbins={
            'start': 0,
            'end': ceil(max(df.x)),
            'size': 1
        }
    )
    fig.update_layout(title='Lab turnaround time')
    fig.update_xaxes(title='Days')
    fig.update_yaxes(title='Probability')
    return fig
