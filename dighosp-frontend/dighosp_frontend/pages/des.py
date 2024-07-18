"""Home page for the Digital Hospitals app."""

import base64

import dash
import dash_bootstrap_components as dbc
import requests
from dash import Input, Output, State, callback, dcc, html
from dash_ag_grid import AgGrid
from dash_compose import composition
from humanize import naturalsize

from dighosp_frontend.components import breadcrumb
from dighosp_frontend.conf import DES_FASTAPI_URL

dash.register_page(__name__, path='/des')
LABELS = ['🏠 Home', 'Simulation']
PATHS = ['des']

COLDEFS_SUBMITTED_JOBS = [
    {
        'field': 'id',
        'headerName': 'ID'
    }, {
        # Column is not actually sortable since there is only one option, but this displays
        # a down arrow in the column header
        'field': 'submitted',
        'sort': 'desc',
        'sortable': True,
        'sortingOrder': ['desc'],
        'cellRenderer': 'unix_to_str'
    }, {
        'headerName': 'progress',
        'valueGetter': {'function': "`${params.data.progress}/${params.data.max_progress}`"}
    }, {
        # cellRenderer creates link to results if valueGetter returns non-empty string
        'headerName': 'Result',
        'valueGetter': {
            'function': "params.data.progress == params.data.max_progress ? params.data.id : ''"
        },
        'cellRenderer': 'des_result_link'
    }
]


@composition
def layout():
    """Page layout"""
    with html.Div() as ret:
        yield breadcrumb(LABELS, PATHS)
        yield html.H1('Histopathology Process Simulation')
        yield dcc.Interval('interval-refresh-sim-list', 5000)
        with dbc.Card(class_name='mb-3'):
            with dbc.CardBody():
                yield html.H4('New Simulation Job', className='card-title')
                yield row_file_io()
                yield sim_controls()
                yield sim_modal()
        with dbc.Card(class_name='mb-3'):
            with dbc.CardBody():
                yield html.H4('Submitted Jobs', className='card-title')
                yield html.Div(id='div-des-refresh-status', className='mb-3 error-msg')
                yield AgGrid(
                    id='ag_grid-des-list',
                    rowData=[],
                    defaultColDef={'sortable': False},
                    columnDefs=COLDEFS_SUBMITTED_JOBS,
                    columnSize='responsiveSizeToFit'
                )
    return ret


@composition
def row_file_io():
    """Upload and download buttons for the DES service.

    The download button provides an example Excel file for the simulation configuration.
    """
    with dbc.Row() as ret:
        with dbc.Col(width='auto'):
            with dbc.Button(
                id='btn-des-download-example',
                href=dash.get_asset_url('config_base.xlsx'),
                external_link=True
            ):
                yield "Download example configuration"
        with dbc.Col(width='auto', class_name='mb-3 ps-0'):
            with dcc.Upload(
                id='upload-des-new',
                accept='.xlsx'
            ):
                with dbc.Button():
                    yield "Upload config file"
        with dbc.Label(width='auto', class_name='mb-3 ps-0'):
            with html.Span(id='span-des-new-status'):
                yield 'No file selected.'
    return ret


@composition
def sim_controls():
    """Controls for setting simulation parameters (in addition to those provided by the uploaded
    Excel file).
    """
    with dbc.Row() as ret:
        with dbc.Label(width='auto', class_name='ps-0'):
            yield 'Simulation length (weeks):'
        with dbc.Col(class_name='ms-0 me-2 px-0', width='auto',
                     style={'width': '130px'}):
            yield dbc.Input(
                id='number-des-new-sim-weeks',
                type='number', min=0, max=100, value=10, step=1
            )
        with dbc.Label(width='auto'):
            yield '# of replications:'
        with dbc.Col(class_name='mx-0 me-2 px-0', width='auto',
                     style={'width': '130px'}):
            yield dbc.Input(
                id='number-des-new-sim-reps',
                type='number', min=1, max=999, step=1, value=30
            )
        with dbc.Label(width='auto'):
            yield 'Runner speed:'
        with dbc.Col(class_name='mx-0 px-0 ', width='auto',
                     style={'width': '130px'}):
            yield dbc.Input(
                id='number-des-new-runner-speed',
                type='number', min=0.01, max=9.99, step=0.01, value=1.2
            )
        with dbc.Label(width='auto', class_name='me-3 ps-1'):
            yield html.Span('m/s')
        with dbc.Col(class_name='mx-0 ps-0', width='auto'):
            with dbc.Button(id='btn-des-new-submit'):
                yield "Submit!"
    return ret


@composition
def sim_modal():
    """Modal dialog for showing the results of submitting a new simulation job."""
    with dbc.Modal(id='modal-des-new',
                   is_open=False,
                   backdrop='static') as ret:
        with dbc.ModalHeader():
            with dbc.ModalTitle(id='modal_title-des-new'):
                yield 'Title'
        with dbc.ModalBody(id='modal_body-des-new'):
            yield 'Body'
        with dbc.ModalFooter():
            with dbc.Button(
                id="btn-des-new-modal-close", className="ms-auto"
            ):
                yield 'Close'
    return ret


@callback(
    Output('span-des-new-status', 'children'),
    Input('upload-des-new', 'contents'),
    State('upload-des-new', 'filename'),
    prevent_initial_call=True
)
def new_file(contents: str | None, filename: str | None):
    if contents is None or filename is None:
        """Callback for new file upload."""
        return dash.no_update

    _, content_str = contents.split(',')
    decoded = base64.b64decode(content_str)
    return f'Uploaded "{filename}", length: {naturalsize(len(decoded))}'


@callback(
    Output('btn-des-new-submit', 'disabled'),
    Input('upload-des-new', 'contents'),
    Input('number-des-new-sim-weeks', 'value'),
    Input('number-des-new-sim-reps', 'value'),
    Input('number-des-new-runner-speed', 'value')
)
def check_form(file_contents: str | None,
               sim_weeks: int | None,
               sim_reps: int | None,
               runner_speed: float | None):
    """Check form input and enable/disable the Submit button accordingly.

    The input is None if no file is uploaded or the value of an Input element is invalid."""
    if None in (file_contents, sim_weeks, sim_reps, runner_speed):
        return True
    return False


@callback(
    Output('modal_title-des-new', 'children'),
    Output('modal_body-des-new', 'children'),
    Output('modal-des-new', 'is_open'),
    Input('btn-des-new-submit', 'n_clicks'),
    State('upload-des-new', 'contents'),
    State('number-des-new-sim-weeks', 'value'),
    State('number-des-new-sim-reps', 'value'),
    State('number-des-new-runner-speed', 'value'),
    prevent_initial_call=True
)
def submit(_,
           file_contents: str,
           sim_weeks: int,
           sim_reps: int,
           runner_speed: float):
    """Submit the simulation job on button click."""
    _, content_string = file_contents.split(',')
    file_bytes = base64.b64decode(content_string)

    try:
        response = requests.post(
            f'{DES_FASTAPI_URL}/jobs',
            files={'config_bytes': file_bytes},
            data={
                'sim_hours': sim_weeks * 168.0,
                'num_reps': sim_reps,
                'runner_speed': runner_speed,
            },
            timeout=10
        )
    except requests.ConnectionError:
        return (
            'Error',
            'Could not connect to the backend server',
            True
        )
    except requests.Timeout:
        return (
            'Error',
            'Request timed out',
            True
        )
    except requests.RequestException:  # Base exception for requests module
        return (
            'Error',
            'Unknown request exception',
            True
        )

    if response.status_code != 202:  # 202 Accepted
        return 'Error', f"HTTP status code {response.status_code}", True

    obj_id = response.json()['id']
    return 'Job created!', f"ID: {obj_id}", True


@callback(
    Output('modal-des-new', 'is_open', allow_duplicate=True),
    Input('btn-des-new-modal-close', 'n_clicks'),
    prevent_initial_call=True
)
def close_modal(_):
    """Close the modal dialog."""
    return False


@callback(
    Output('div-des-refresh-status', 'children'),
    Output('ag_grid-des-list', 'rowData'),
    Input('interval-refresh-sim-list', 'n_intervals')
)
def refresh_grid(_):
    """Refresh the list of simulation jobs."""
    try:
        response = requests.get(
            f'{DES_FASTAPI_URL}/jobs',
            timeout=10
        )
    except requests.ConnectionError:
        return (
            'Error: Could not connect to the backend server',
            dash.no_update
        )
    except requests.Timeout:
        return (
            'Error: Request timed out',
            dash.no_update
        )
    except requests.RequestException:  # Base exception for requests module
        return (
            'Error: Unknown request exception',
            dash.no_update
        )

    if response.status_code != 200:  # OK
        return f"Error: HTTP status code {response.status_code}", dash.no_update

    return '', response.json()
