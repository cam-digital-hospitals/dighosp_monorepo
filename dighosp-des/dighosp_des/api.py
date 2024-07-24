"""FastAPI endpoints for the Discrete-event simulation module."""

import json
from datetime import datetime
from os import PathLike
from tempfile import NamedTemporaryFile
from typing import Annotated, Optional, Sequence

import orjson
import pydantic as pyd
from bson import ObjectId
from fastapi import FastAPI, File, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from gridfs import GridFS
from openpyxl import load_workbook
from pydantic.functional_validators import AfterValidator
from pymongo import MongoClient
from rq import Queue

from .conf import MONGO_CLIENT_ARGS
from .config import Config
from .kpis import lab_tats_fig, utilisation_fig, wips_fig
from .model import Model
from .redis_worker import RedisSingleton


def assert_object_id(s: str):
    """Assert that a given string is a valid BSON ObjectId and return the string."""
    assert ObjectId.is_valid(s)
    return s


ObjectIdStr = Annotated[str, AfterValidator(assert_object_id)]


class SimJob(pyd.BaseModel):
    """A simulation job for the histopathology department model."""

    # TODO: store precomputed KPIs
    #
    # For Redis Queue (RQ), we can use the `depends_on` argument of Job.enqueue()
    # to compute the KPIs only when all simulation replications are completed sucessfully.

    config: Config = pyd.Field(
        title='Config file ID',
        description='Simulation configuration.'
    )
    """Simulation configuration object."""

    submitted: float = pyd.Field(
        default_factory=lambda: datetime.now().timestamp(),
        title='Submitted',
        examples=[datetime(2024, 6, 4).timestamp()]
    )
    """UNIX timestamp representing the submission time of the simulation job."""

    results_ids: Sequence[Optional[ObjectIdStr]] = pyd.Field(
        title='Result file Object IDs',
    )
    """Object IDs of the result files for the simulation job, one per simulation replication.
    Results files are stored using GridFS."""

    results_kpi_obj_id: Optional[ObjectIdStr] = pyd.Field(
        title='Simulation results KPIs',
        default=None
    )
    """Pointer to a dict of Plotly objects, (e.g. `Figure`), for displaying KPIs. The objects are
    themselves encoded as dicts."""


class JobSubmitResult(pyd.BaseModel):
    """Result of a `submit()` function call."""

    id: ObjectIdStr = pyd.Field(
        title='Job ID',
        examples=['542c2b97bac0595474108b48']
    )
    """ObjectId of the DES job in the MongoDB database."""


class JobSummary(pyd.BaseModel):
    """Summary of a submitted simulation job."""
    id: ObjectIdStr
    submitted: float
    progress: pyd.NonNegativeInt
    max_progress: pyd.NonNegativeInt


app = FastAPI(
    title='Digital Hospitals \u2014 DES module',
    description="""\
Provides endpoints for launching simulations of the histopathology lab model and \
querying the results.""",
    redoc_url=None  # only use Swagger UI,
)


@app.get('/', include_in_schema=False)
def root_to_docs(request: Request):
    """Redirect root to /docs."""
    return RedirectResponse(f"{request.scope.get("root_path")}/docs")


@app.post(
    '/jobs',
    summary='Submit',
    status_code=status.HTTP_202_ACCEPTED,
    response_description='Job accepted'
)
def submit(
    config_bytes: Annotated[bytes, File(description='Config file (.xlsx) as a `bytes` object.')],
    sim_hours: Annotated[float, Form(
        title='Number of replications',
        description='Number of replications to run the simulation for.',
        gt=0,
        examples=[1680]
    )],
    num_reps: Annotated[int, Form(
        title='Number of replications',
        description='Number of replications to run the simulation for.',
        gt=0,
        examples=[30]
    )],
    runner_speed: Annotated[float, Form(
        title='Runner speed',
        description='Runner speed in m/s',
        gt=0,
        examples=[1.2]
    )]
) -> JobSubmitResult:
    """Submit a new simulation job to the database and launch it."""
    with NamedTemporaryFile(delete_on_close=False, suffix='.xlsx') as fp:
        fp.write(config_bytes)
        fp.close()
        obj_id = new_sim(fp.name, sim_hours, num_reps, runner_speed)
        return JobSubmitResult(id=str(obj_id))


def new_sim(
        xlsx_path: PathLike,
        sim_hours: float,
        num_reps: int,
        runner_speed: float
) -> ObjectIdStr:
    """Set up a new simulation job."""
    try:
        conf = Config.from_workbook(
            load_workbook(xlsx_path, data_only=True),
            sim_hours, num_reps, runner_speed
        )
    except Exception as e:
        raise ValueError(f'Could not parse {xlsx_path}: \n\n {str(e)}') from e

    # Add simulation job to the 'sim' database
    results_ids: Sequence[Optional[ObjectIdStr]] = [None]*(conf.num_reps)
    job = SimJob(config=conf, results_ids=results_ids)
    with MongoClient(**MONGO_CLIENT_ARGS) as client:
        coll = client['sim']['sim_jobs']
        _id = coll.insert_one(job.model_dump()).inserted_id

    jobs = []
    for idx in range(num_reps):
        queue: Queue = RedisSingleton().work_queue
        job = queue.enqueue(sim_replication, ObjectIdStr(_id), idx)
        jobs.append(job)
    queue.enqueue(save_dash_objs, ObjectIdStr(_id), depends_on=jobs)

    return ObjectIdStr(_id)


def sim_replication(job_id: ObjectIdStr, idx: int) -> ObjectId:
    """Run one replication of the simulation job defined by `job_id` and write the results to
    a file. Update the simulation job entry with the new file's ObjectId and return the
    ObjectId."""
    # The actual simulation. A Dockerized version of this function may read the job_id
    # and idx from environment variables.
    with MongoClient(**MONGO_CLIENT_ARGS) as client:
        coll = client['sim']['sim_jobs']
        obj = coll.find_one({'_id': ObjectId(job_id)})
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No simulation job with ObjectId {job_id}."
            )
        job = SimJob.model_validate(obj)
        model = Model(job.config)
        model.run()
        output = model.result_dump()

        output_bytes = orjson.dumps(output)

        fs = GridFS(client['sim'])
        obj_id = fs.put(output_bytes)

        # write output to job.results_ids[idx]
        coll.find_one_and_update(
            filter={'_id': ObjectId(job_id)},
            update={'$set': {f'results_ids.{idx}': str(obj_id)}}
        )

        return obj_id


def save_dash_objs(job_id: ObjectIdStr):
    """Compute a dict of figure data to display on the frontend later. Save the dict to the
    MongoDB database."""
    n = get_status(job_id).max_progress
    data = [get_result(job_id, idx) for idx in range(n)]
    kpi_objs = {
        'utilisation': utilisation_fig(data),
        'wip': wips_fig(data, wip='Total WIP'),
        'tat': lab_tats_fig(data)
    }
    
    with MongoClient(**MONGO_CLIENT_ARGS) as client:
        coll = client['sim']['sim_jobs']
        obj = coll.find_one({'_id': ObjectId(job_id)})
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No simulation job with ObjectId {job_id}."
            )
        
        output_bytes = orjson.dumps(kpi_objs)

        fs = GridFS(client['sim'])
        obj_id = fs.put(output_bytes)
        
        coll.find_one_and_update(
            filter={'_id': ObjectId(job_id)},
            update={'$set': {'results_kpi_obj_id': str(obj_id)}}
        )
    return obj_id

@app.get(
    '/jobs/{job_id}/results/dash_objs',
    summary='Get Plotly Dash objects'
)
def get_dash_objs(job_id: ObjectIdStr):
    """Get the Plotly object data required for displaying KPIs on the frontend.

    For example, a Plotly Figure can be serialised using `data = fig.to_dict()` and restored using
    `fig = Figure(data)`.
    """
    with MongoClient(**MONGO_CLIENT_ARGS) as client:
        coll = client['sim']['sim_jobs']
        obj = coll.find_one({'_id': ObjectId(job_id)})
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No simulation job with ObjectId {job_id}."
            )
        
        fs = GridFS(client['sim'])
        obj_id = ObjectId(obj['results_kpi_obj_id'])
        return json.load(fs.get(obj_id))

@app.get(
    '/jobs',
    summary='List jobs'
)
def list_jobs() -> list[JobSummary]:
    """List all jobs."""
    with MongoClient(**MONGO_CLIENT_ARGS) as client:
        coll = client['sim']['sim_jobs']
        lst = list(coll.find({}))
        return [
            JobSummary(
                id=ObjectIdStr(x['_id']),
                submitted=x['submitted'],
                progress=sum(0 if s is None else 1 for s in x['results_ids']),
                max_progress=len(x['results_ids'])
            ) for x in lst
        ]


@app.get(
    '/jobs/{job_id}/status',
    summary='Job status'
)
def get_status(job_id: ObjectIdStr) -> JobSummary:
    """Query the completion status of a simulation job."""
    with MongoClient(**MONGO_CLIENT_ARGS) as client:
        coll = client['sim']['sim_jobs']
        x = coll.find_one({'_id': ObjectId(job_id)})
        if x is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No simulation job with ObjectId {job_id}."
            )
        return JobSummary(
            id=ObjectIdStr(x['_id']),
            submitted=x['submitted'],
            progress=sum(0 if s is None else 1 for s in x['results_ids']),
            max_progress=len(x['results_ids'])
        )


@app.get(
    '/jobs/{job_id}/result_ids',
    summary='Result Ids'
)
def get_result_ids(job_id: ObjectIdStr) -> Sequence[Optional[ObjectIdStr]]:
    """Fetch the ObjectIds of the result files of a given simulation job."""
    with MongoClient(**MONGO_CLIENT_ARGS) as client:
        coll = client['sim']['sim_jobs']
        x = coll.find_one({'_id': ObjectId(job_id)})
        if x is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No simulation job with ObjectId {job_id}."
            )
        return x['results_ids']


@app.get(
    '/jobs/{job_id}/results/{idx}',
    summary='Simulation replication result'
)
def get_result(job_id: ObjectIdStr, idx: int) -> dict[str, dict]:
    """Return the result of a single simulation replication."""
    with MongoClient(**MONGO_CLIENT_ARGS) as client:
        coll = client['sim']['sim_jobs']
        obj = coll.find_one({'_id': ObjectId(job_id)})
        if obj is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No simulation job with ObjectId {job_id}."
            )
        job = SimJob.model_validate(obj)

        result_id = job.results_ids[idx]
        if result_id is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Result #{idx} for Job {job_id} not available."
            )

        fs = GridFS(client['sim'])
        return orjson.loads(fs.get(ObjectId(result_id)).read())
