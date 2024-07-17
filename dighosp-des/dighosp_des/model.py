"""Module containing the simulation model for the histopathology lab."""

import dataclasses as dc
import random
from dataclasses import dataclass
from typing import Literal, Self

import dacite
import salabim as sim

from .config import BatchSizes, Config, ResourcesInfo
from .distributions import (PERT, Constant, Distribution, IntConstant, IntDistribution,
                            IntDistributionInfo, IntPERT, IntTri, Tri)
from .process import (ArrivalGenerator, BaseProcess, ResourceScheduler, p10_reception, p20_cutup,
                      p30_processing, p40_microtomy, p50_staining, p60_labelling, p70_scanning,
                      p80_qc, p90_reporting)

STRICT = dacite.Config(strict=True)


class Model(sim.Environment):
    """The histopathology simulation model class."""

    num_reps: int
    """The number of simulation replications to run the model."""

    sim_length: float
    """The duration of each simulation replication."""

    resources: 'Resources'
    """The resources associated with this model, as a dataclass instance."""

    task_durations: 'TaskDurations'
    """Dataclass instance containing the task durations for the model."""

    batch_sizes: BatchSizes
    """Dataclass instance containing the batch sizes for various tasks in the model."""

    globals: 'Globals'
    """Dataclass instance containing global variables for the model."""

    runner_times: 'RunnerTimes'
    """Dataclass instance containing runner times between histopathology stages as well
    as the duration of additional runner tasks."""

    rng: random.Random
    """Random number generator for the `Model` object."""

    specimen_data: dict[str, dict]
    """Dict containing specimen attributes for all specimens in the simulation model
    (in-progress or completed)."""

    wips: 'Wips'
    """Dataclass instance containing work-in-progress counters for the model."""

    processes: dict[str, BaseProcess]
    """Dict mapping names (str) to the processes of the simulation model."""

    def __init__(self, config: Config, **kwargs):
        # Change constructor defaults
        kwargs['time_unit'] = kwargs.get('time_unit', 'hours')
        kwargs['random_seed'] = kwargs.get('random_seed', '')
        super().__init__(**kwargs, config=config)

    def setup(self, **kwargs) -> None:
        """Set up the component, called immediately after initialisation."""
        config: Config = kwargs.pop('config')
        super().setup()

        self.num_reps = config.num_reps
        self.sim_length = self.env.hours(config.sim_hours)
        self.rng = random.Random()

        # ARRIVALS
        ArrivalGenerator(
            'Arrival Generator (cancer)',
            schedule=config.arrivals.cancer,
            env=self,
            # kwargs
            cancer=True
        )
        ArrivalGenerator(
            'Arrival Generator (noncancer)',
            schedule=config.arrivals.noncancer,
            env=self,
            # kwargs
            cancer=False
        )

        self.resources = Resources(self)
        for f in dc.fields(self.resources):
            ResourceScheduler(
                f'Scheduler [{f.name}]',
                resource=getattr(self.resources, f.name),
                schedule=getattr(config.resources, f.name).schedule,
                env=self
            )

        self.task_durations = TaskDurations.from_config(env=self, config=config)
        self.batch_sizes = config.batch_sizes
        self.globals = Globals.from_config(env=self, config=config)
        self.runner_times = RunnerTimes.from_config(env=self, config=config)

        ##########################
        ### END PARSING CONFIG ###
        ##########################

        self.specimen_data = {}
        self.wips = Wips(self)

        # Register processes
        self.processes: dict[str, BaseProcess] = {}
        p10_reception.register_processes(self)
        p20_cutup.register_processes(self)
        p30_processing.register_processes(self)
        p40_microtomy.register_processes(self)
        p50_staining.register_processes(self)
        p60_labelling.register_processes(self)
        p70_scanning.register_processes(self)
        p80_qc.register_processes(self)
        p90_reporting.register_processes(self)

        self.u01 = sim.Uniform(0, 1, randomstream=self.rng, env=self)

    def run(self) -> None:  # pylint: disable=arguments-differ
        super().run(duration=self.sim_length)

    def result_dump(self) -> dict:
        """Serialise the model's state, for logging/KPI computation/etc."""
        def res_tx_as_dict(res, fn):
            t, x = fn(res).tx()
            return list(zip(list(t), list(x)))

        def wip_tx_as_dict(wip):
            t, x = wip.tx()
            return list(zip(list(t), list(x)))

        res_claimed = {res.name(): res_tx_as_dict(res, lambda res: res.claimed_quantity)
                       for res in self.resources.__dict__.values()}
        res_waiting = {res.name(): res_tx_as_dict(res, lambda res: res.requesters().length)
                       for res in self.resources.__dict__.values()}
        res_capacity = {res.name(): res_tx_as_dict(res, lambda res: res.capacity)
                        for res in self.resources.__dict__.values()}
        res_current_claimers = {res.name(): [x.name() for x in res.claimers()]
                                for res in self.resources.__dict__.values()}
        res_current_requesters = {res.name(): [x.name() for x in res.requesters()]
                                  for res in self.resources.__dict__.values()}

        dict_res = {
            'n_claimed': res_claimed,
            'n_waiting': res_waiting,
            'capacity': res_capacity,
            'current_claimers': res_current_claimers,
            'current_requesters': res_current_requesters
        }
        wips = {wip.name(): wip_tx_as_dict(wip) for wip in self.wips.__dict__.values()}

        dump = {
            'resources': dict_res,
            'wips': wips,
            'specimen_data': self.specimen_data
        }

        return dump


@dataclass(kw_only=True, eq=False)
class Resources:
    """Dataclass for tracking the resources of a Model."""
    booking_in_staff: sim.Resource
    bms: sim.Resource
    cut_up_assistant: sim.Resource
    processing_room_staff: sim.Resource
    microtomy_staff: sim.Resource
    staining_staff: sim.Resource
    scanning_staff: sim.Resource
    qc_staff: sim.Resource
    histopathologist: sim.Resource
    bone_station: sim.Resource
    processing_machine: sim.Resource
    staining_machine: sim.Resource
    coverslip_machine: sim.Resource
    scanning_machine_regular: sim.Resource
    scanning_machine_megas: sim.Resource

    def __init__(self, env: Model) -> None:
        # For each field `f` in this dataclass, construct a Resource from the
        # ResourcesInfo field with the same name.
        for f in dc.fields(self):
            self.__setattr__(
                f.name,
                sim.Resource(
                    name=ResourcesInfo.model_fields[f.name].title,
                    env=env
                )
            )


@dataclass(kw_only=True, eq=False)
class TaskDurations:
    """Dataclass for tracking task durations in a Model."""
    receive_and_sort: Distribution
    pre_booking_in_investigation: Distribution
    booking_in_internal: Distribution
    booking_in_external: Distribution
    booking_in_investigation_internal_easy: Distribution
    booking_in_investigation_internal_hard: Distribution
    booking_in_investigation_external: Distribution
    cut_up_bms: Distribution
    cut_up_pool: Distribution
    cut_up_large_specimens:  Distribution
    load_bone_station: Distribution
    decalc: Distribution
    unload_bone_station: Distribution
    load_into_decalc_oven: Distribution
    unload_from_decalc_oven: Distribution
    load_processing_machine: Distribution
    unload_processing_machine: Distribution
    processing_urgent: Distribution
    processing_small_surgicals: Distribution
    processing_large_surgicals: Distribution
    processing_megas: Distribution
    embedding: Distribution
    embedding_cooldown: Distribution
    block_trimming: Distribution
    microtomy_serials: Distribution
    microtomy_levels: Distribution
    microtomy_larges: Distribution
    microtomy_megas: Distribution
    load_staining_machine_regular: Distribution
    load_staining_machine_megas: Distribution
    staining_regular: Distribution
    staining_megas: Distribution
    unload_staining_machine_regular: Distribution
    unload_staining_machine_megas: Distribution
    load_coverslip_machine_regular: Distribution
    coverslip_regular: Distribution
    coverslip_megas: Distribution
    unload_coverslip_machine_regular: Distribution
    labelling: Distribution
    load_scanning_machine_regular: Distribution
    load_scanning_machine_megas: Distribution
    scanning_regular: Distribution
    scanning_megas: Distribution
    unload_scanning_machine_regular: Distribution
    unload_scanning_machine_megas: Distribution
    block_and_quality_check: Distribution
    assign_histopathologist: Distribution
    write_report: Distribution

    @staticmethod
    def time_unit_full(abbr: Literal['s', 'm', 'h']):
        """Obtain salabim time-unit strings from one-letter abbreviations."""
        return "seconds" if abbr == 's' else "minutes" if abbr == 'm' else "hours"

    @classmethod
    def from_config(cls, env: Model, config: Config) -> Self:
        """Construct a `TaskDurations` instance from a `Config` instance."""
        task_durations = {
            key: (
                PERT(
                    val.low, val.mode, val.high,
                    time_unit=cls.time_unit_full(val.time_unit),
                    randomstream=env.rng,
                    env=env
                ) if val.type == 'PERT' else
                Tri(
                    val.low, val.mode, val.high,
                    time_unit=cls.time_unit_full(val.time_unit),
                    randomstream=env.rng,
                    env=env
                ) if val.type == 'Tri' else
                Constant(
                    val.mode,
                    time_unit=cls.time_unit_full(val.time_unit),
                    randomstream=env.rng,
                    env=env
                )
            ) for key, val in iter(config.task_durations)
        }
        return dacite.from_dict(cls, task_durations, STRICT)


@dataclass(kw_only=True, eq=False)
class Wips:
    """Dataclass for tracking work-in-progress counters for the Model simulation."""
    total: sim.Monitor
    in_reception: sim.Monitor
    in_cut_up: sim.Monitor
    in_processing: sim.Monitor
    in_microtomy: sim.Monitor
    in_staining: sim.Monitor
    in_labelling: sim.Monitor
    in_scanning: sim.Monitor
    in_qc: sim.Monitor
    in_reporting: sim.Monitor

    def __init__(self, env: 'Model') -> None:
        monitor_args = {'level': True, 'type': 'uint32', 'env': env}
        self.total = sim.Monitor('Total WIP', **monitor_args)
        self.in_reception = sim.Monitor('Reception', **monitor_args)
        self.in_cut_up = sim.Monitor('Cut-up', **monitor_args)
        self.in_processing = sim.Monitor('Processing', **monitor_args)
        self.in_microtomy = sim.Monitor('Microtomy', **monitor_args)
        self.in_staining = sim.Monitor('Staining', **monitor_args)
        self.in_labelling = sim.Monitor('Labelling', **monitor_args)
        self.in_scanning = sim.Monitor('Scanning', **monitor_args)
        self.in_qc = sim.Monitor('QC', **monitor_args)
        self.in_reporting = sim.Monitor('Reporting', **monitor_args)


@dataclass
class Globals:
    """Dataclass for global model variables."""
    prob_internal: float
    prob_urgent_cancer: float
    prob_urgent_non_cancer: float
    prob_priority_cancer: float
    prob_priority_non_cancer: float
    prob_prebook: float
    prob_invest_easy: float
    prob_invest_hard: float
    prob_invest_external: float
    prob_bms_cutup: float
    prob_bms_cutup_urgent: float
    prob_large_cutup: float
    prob_large_cutup_urgent: float
    prob_pool_cutup: float
    prob_pool_cutup_urgent: float
    prob_mega_blocks: float
    prob_decalc_bone: float
    prob_decalc_oven: float
    prob_microtomy_levels: float
    num_blocks_large_surgical: IntDistribution
    num_blocks_mega: IntDistribution
    num_slides_larges: IntDistribution
    num_slides_levels: IntDistribution
    num_slides_megas: IntDistribution
    num_slides_serials: IntDistribution

    @classmethod
    def from_config(cls, env: Model, config: Config) -> Self:
        """Construct a `Globals` instance from a `Config` instance."""

        global_vars = {
            # process fields by type
            key: (
                (
                    IntPERT(val.low, val.mode, val.high, randomstream=env.rng, env=env)
                    if val.type == 'IntPERT'
                    else IntTri(val.low, val.mode, val.high, randomstream=env.rng, env=env)
                    if val.type == 'IntTriangular'
                    else IntConstant(val.mode, randomstream=env.rng, env=env)
                ) if isinstance(val, IntDistributionInfo)
                else val
            ) for key, val in iter(config.global_vars)
        }
        return dacite.from_dict(cls, global_vars, STRICT)


@dataclass
class RunnerTimes:
    """Dataclass for runner times."""
    reception_cutup: float
    cutup_processing: float
    processing_microtomy: float
    microtomy_staining: float
    staining_labelling: float
    labelling_scanning: float
    scanning_qc: float

    extra_loading: float
    extra_unloading: float

    @classmethod
    def from_config(cls, env: Model, config: Config) -> Self:
        """Construct a `RunnerTimes` instance from a `Config` instance."""
        runner_times = {
            k: env.seconds(v)
            for k, v in iter(config.runner_times)
        }
        return dacite.from_dict(cls, runner_times, STRICT)
