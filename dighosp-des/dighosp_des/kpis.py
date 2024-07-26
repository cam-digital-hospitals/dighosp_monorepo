import json
from itertools import chain
from math import ceil

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


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
    return json.loads(fig.to_json())


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
    return json.loads(fig.to_json())


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
    return json.loads(fig.to_json())
