"""Defines dataclasses for the histopathology simulation model configuration parameters."""

from typing import Annotated, Literal, Self, Sequence

import pandas as pd
import pydantic as pyd
from annotated_types import Ge, Le, Len
from openpyxl import Workbook

from .distributions import DistributionInfo, IntDistributionInfo
from .excel import get_name, get_table

Probability = Annotated[float, Ge(0), Le(1)]
STAFF_ATTR = {'json_schema_extra': {'resource_type': 'staff'}}
MACHINE_ATTR = {'json_schema_extra': {'resource_type': 'machine'}}


class Config(pyd.BaseModel):
    """Top-level dataclass for the simulation configuration."""

    arrivals: 'ArrivalSchedules' = pyd.Field(title='Arrival Schedules')
    """The arrival schedules for cancer and non-cancer specimen arrivals."""

    batch_sizes: 'BatchSizes' = pyd.Field(title='Batch sizes')
    """Batch sizes for delivery and machine tasks."""

    global_vars: 'Globals' = pyd.Field(title='Global variables')
    """Global variables for the simulation environment, e.g., branching probabilities of
    the histopathology process."""

    resources: 'ResourcesInfo' = pyd.Field(title='Resource information')
    """Configuration data for the resources of the simulation model."""

    runner_times: 'RunnerTimesConfig' = pyd.Field(title='Runner times')
    """Durations for transporting specimens between stages, as well as additional runner tasks."""

    task_durations: 'TaskDurationsInfo' = pyd.Field(title='Task Durations')
    """Durations for the individual steps of the histopathology process."""

    sim_hours: pyd.PositiveFloat = pyd.Field(title='Simulation length (hours)')
    """Simulation length in hours."""

    num_reps: pyd.PositiveInt = pyd.Field(title='# of replications')
    """Number of simulation replications."""

    @classmethod
    def from_workbook(
        cls,
        wbook: Workbook,
        sim_hours: float,
        num_reps: int,
        runner_speed: float | None = None
    ) -> Self:
        """Load a config from an Excel workbook."""
        arrival_schedules = ArrivalSchedules.from_workbook(wbook)
        resources = ResourcesInfo.from_workbook(wbook)
        task_durations = TaskDurationsInfo.from_workbook(wbook)
        batch_sizes = BatchSizes.from_workbook(wbook)
        global_vars = Globals.from_workbook(wbook)
        runner_cfg = RunnerTimesConfig.from_workbook(wbook, speed=runner_speed)

        return cls(
            arrivals=arrival_schedules,
            batch_sizes=batch_sizes,
            global_vars=global_vars,
            resources=resources,
            runner_times=runner_cfg,
            task_durations=task_durations,
            sim_hours=sim_hours,
            num_reps=num_reps
        )


# ARRIVALS
class ArrivalSchedule(pyd.BaseModel):
    """An arrival schedule for specimens."""

    rates: Annotated[Sequence[pyd.NonNegativeFloat], Len(168, 168)] = pyd.Field(
        title='Arrival rates'
    )
    """Hourly arrival rates for the arrival process, for one week (168 hours)."""

    @classmethod
    def from_pd(cls, df: pd.DataFrame) -> Self:
        """Construct an arrival schedule from a dataframe with the 24 hours the day as rows
        and the seven days of the week as columns (starting on Monday).  Each value is the
        arrival rate for one hour of the week."""
        return cls(rates=df.to_numpy().flatten('F').tolist())  # F = column-major order


class ArrivalSchedules(pyd.BaseModel):
    """Dataclass for tracking the specimen arrival schedules of the histopathology model."""

    cancer: ArrivalSchedule = pyd.Field('Arrival rates, cancer')
    """Arrival schedule for cancer-pathway specimens."""

    noncancer: ArrivalSchedule = pyd.Field('Arrival rates, non-cancer')
    """Arrival schedule for non-cancer-pathway specimens."""

    @classmethod
    def from_workbook(cls, wbook: Workbook) -> Self:
        """Construct a dataclass instance from an Excel workbook."""
        arr_sch_cancer_df = (
            df := pd.DataFrame(
                (table := get_table(wbook, 'Arrival Schedules',
                 'ArrivalScheduleCancer'))[1:],
                columns=table[0]
            ).set_index('Hour')
        ).loc[df.index != 'Total']

        arr_sch_noncancer_df = (
            df := pd.DataFrame(
                (table := get_table(wbook, 'Arrival Schedules',
                 'ArrivalScheduleNonCancer'))[1:],
                columns=table[0]
            ).set_index('Hour')
        ).loc[df.index != 'Total']

        return cls(
            cancer=ArrivalSchedule.from_pd(arr_sch_cancer_df),
            noncancer=ArrivalSchedule.from_pd(arr_sch_noncancer_df),
        )


# RESOURCES
class ResourceSchedule(pyd.BaseModel):
    """A resource allocation schedule."""

    day_flags: Annotated[Sequence[bool], Len(7, 7)] = pyd.Field(title='Day flags')
    """True if resource is scheduled for the day (MON to SUN), False otherwise."""

    allocation: Annotated[Sequence[pyd.NonNegativeInt], Len(48, 48)] = pyd.Field(
        title='Resource allocation'
    )
    """Number of resource units allocated for the day (in 30-min intervals), if the corresponding
    day flag is set to 1."""

    @classmethod
    def from_pd(cls, df: pd.DataFrame, row_name: str) -> Self:
        """Construct a resource schedule from a DataFrame row. The columns of the dataframe must
        include 'MON' to 'SUN' in order and '00:00' to '23:30' in order (in 30min intervals)."""
        return cls(
            day_flags=df.loc[row_name, 'MON':'SUN'].tolist(),
            allocation=df.loc[row_name, '00:00':'23:30'].tolist()
        )


class ResourceInfo(pyd.BaseModel):
    """Contains information about a resource."""
    name: str = pyd.Field(title='name', examples=['Scanning machine'])
    """The name of the resource."""

    type: Literal['staff', 'machine'] = pyd.Field(title='Resource type')
    """Whether the resource is a staff or machine resource."""

    schedule: ResourceSchedule = pyd.Field(title='Schedule')
    """A schedule defining the number of allocated resource units over the course of a week."""


class ResourcesInfo(pyd.BaseModel):
    """Dataclass for tracking the staff resources of a model.

    The field titles in this dataclass **MUST** match the rows of the configuration
    Excel template ("Resources" tab)."""
    booking_in_staff: ResourceInfo = pyd.Field(title='Booking-in staff', **STAFF_ATTR)
    bms: ResourceInfo = pyd.Field(title='BMS', **STAFF_ATTR)
    cut_up_assistant: ResourceInfo = pyd.Field(title='Cut-up assistant', **STAFF_ATTR)
    processing_room_staff: ResourceInfo = pyd.Field(title='Processing room staff', **STAFF_ATTR)
    microtomy_staff: ResourceInfo = pyd.Field(title='Microtomy staff', **STAFF_ATTR)
    staining_staff: ResourceInfo = pyd.Field(title='Staining staff', **STAFF_ATTR)
    scanning_staff: ResourceInfo = pyd.Field(title='Scanning staff', **STAFF_ATTR)
    qc_staff: ResourceInfo = pyd.Field(title='QC staff', **STAFF_ATTR)
    histopathologist: ResourceInfo = pyd.Field(title='Histopathologist', **STAFF_ATTR)
    bone_station: ResourceInfo = pyd.Field(title='Bone station', **MACHINE_ATTR)
    processing_machine: ResourceInfo = pyd.Field(title='Processing machine', **MACHINE_ATTR)
    staining_machine: ResourceInfo = pyd.Field(title='Staining machine', **MACHINE_ATTR)
    coverslip_machine: ResourceInfo = pyd.Field(title='Coverslip machine', **MACHINE_ATTR)
    scanning_machine_regular: ResourceInfo = pyd.Field(
        title='Scanning machine (regular)', **MACHINE_ATTR)
    scanning_machine_megas: ResourceInfo = pyd.Field(
        title='Scanning machine (megas)', **MACHINE_ATTR)

    @classmethod
    def from_workbook(cls, wbook: Workbook) -> Self:
        """Construct a dataclass instance from an Excel workbook."""
        resources_df = (
            pd.DataFrame(
                (table := get_table(
                    wbook, 'Resource Allocation', 'Resources'))[1:],
                columns=table[0]
            )
            .fillna(0.)
            .set_index('Resource')
        )
        return cls.model_validate({
            key: ResourceInfo(
                name=field.title,
                type=field.json_schema_extra['resource_type'],
                schedule=ResourceSchedule.from_pd(
                    resources_df, row_name=field.title)
            )
            for key, field in ResourcesInfo.model_fields.items()
        })


# TASK DURATIONS
class TaskDurationsInfo(pyd.BaseModel):
    """Information for tracking task durations in a model.

    The field titles in this class **MUST** match the rows of the Excel input file
    ("Task Durations" tab)."""

    receive_and_sort: DistributionInfo = pyd.Field(title='Receive and sort')
    """Time for reception to receive a new specimen and assign a priority value."""

    pre_booking_in_investigation: DistributionInfo = pyd.Field(title='Pre-booking-in investigation')
    """Time to conduct a pre-booking-in investigation, if required."""

    booking_in_internal: DistributionInfo = pyd.Field(title='Booking-in (internal)')
    """Time to book in the specimen if the specimen was received internally, i.e. it already
    exists on the EPIC sytem."""

    booking_in_external: DistributionInfo = pyd.Field(title='Booking-in (external)')
    """Time to book in the specimen if the specimen was received externally, i.e. a new entry must
    be created on EPIC."""

    booking_in_investigation_internal_easy: DistributionInfo = pyd.Field(
        title='Booking-in investigation (internal, easy)'
    )
    """Time to conduct a booking-in investigation for an internal specimen, if the investigation is
    classified as "easy"."""

    booking_in_investigation_internal_hard: DistributionInfo = pyd.Field(
        title='Booking-in investigation (internal, hard)'
    )
    """Time to conduct a booking-in investigation for an internal specimen, if the investigation is
    classified as "hard"."""

    booking_in_investigation_external: DistributionInfo = pyd.Field(
        title='Booking-in investigation (external)'
    )
    """Time to conduct a booking-in investigation for an external specimen."""

    cut_up_bms: DistributionInfo = pyd.Field(title='Cut-up (BMS)')
    """Time to conduct a BMS cut-up."""

    cut_up_pool: DistributionInfo = pyd.Field(title='Cut-up (pool)')
    """Time to conduct a pool cut-up."""

    cut_up_large_specimens: DistributionInfo = pyd.Field(title='Cut-up (large specimens)')
    """Time to conduct a large specimens cut-up."""

    load_bone_station: DistributionInfo = pyd.Field(title='Load bone station')
    """Time to load a batch of blocks into a bone station."""

    decalc: DistributionInfo = pyd.Field(title='Decalc')
    """Time to decalcify a bony specimen."""

    unload_bone_station: DistributionInfo = pyd.Field(title='Unload bone station')
    """Time to unload a batch of blocks into a bone station."""

    load_into_decalc_oven: DistributionInfo = pyd.Field(title='Load into decalc oven')
    """Time to load a single block into a decalc oven."""

    unload_from_decalc_oven: DistributionInfo = pyd.Field(title='Unload from decalc oven')
    """Time to unload a single block into a bone station."""

    load_processing_machine: DistributionInfo = pyd.Field(title='Load processing machine')
    """Time to load a batch of blocks into a processing machine."""

    unload_processing_machine: DistributionInfo = pyd.Field(title='Unload processing machine')
    """Time to unload a batch of blocks from a processing machine."""

    processing_urgent: DistributionInfo = pyd.Field(title='Processing machine (urgent)')
    """Programme length for the processing of urgent blocks."""

    processing_small_surgicals: DistributionInfo = pyd.Field(
        title='Processing machine (small surgicals)'
    )
    """Programme length for the processing of small surgical blocks."""

    processing_large_surgicals: DistributionInfo = pyd.Field(
        title='Processing machine (large surgicals)'
    )
    """Programme length for the processing of large surgical blocks."""

    processing_megas: DistributionInfo = pyd.Field(title='Processing machine (megas)')
    """Programme length for the processing of mega blocks."""

    embedding: DistributionInfo = pyd.Field(title='Embedding')
    """Time to embed a block in paraffin wax (staffed)."""

    embedding_cooldown: DistributionInfo = pyd.Field(title='Embedding (cooldown)')
    """Time for a wax block to cool (unstaffed task)."""

    block_trimming: DistributionInfo = pyd.Field(title='Block trimming')
    """Time to trim excess wax from the edges of a block."""

    microtomy_serials: DistributionInfo = pyd.Field(title='Microtomy (serials)')
    """Time to produce serial slides from a block."""

    microtomy_levels: DistributionInfo = pyd.Field(title='Microtomy (levels)')
    """Time to produce level slides from a block."""

    microtomy_larges: DistributionInfo = pyd.Field(title='Microtomy (larges)')
    """Time to produce large-section slides from a block. These are regular-sized slides, but with
    larger tissue sections."""

    microtomy_megas: DistributionInfo = pyd.Field(title='Microtomy (megas)')
    """Time to produce mega slides from a mega block."""

    load_staining_machine_regular: DistributionInfo = pyd.Field(
        title='Load staining machine (regular)'
    )
    """Time to load a batch of regular-sized slides into a staining machine."""

    load_staining_machine_megas: DistributionInfo = pyd.Field(title='Load staining machine (megas)')
    """Time to load a batch of mega slides into a staining machine."""

    staining_regular: DistributionInfo = pyd.Field(title='Staining (regular)')
    """Time to stain a batch of regular slides."""

    staining_megas: DistributionInfo = pyd.Field(title='Staining (megas)')
    """Time to stain a batch of mega slides."""

    unload_staining_machine_regular: DistributionInfo = pyd.Field(
        title='Unload staining machine (regular)'
    )
    """Time to unload a batch of regular slides from a staining machine."""

    unload_staining_machine_megas: DistributionInfo = pyd.Field(
        title='Unload staining machine (megas)'
    )
    """Time to unload a batch of mega slides from a staining machine."""

    load_coverslip_machine_regular: DistributionInfo = pyd.Field(
        title='Load coverslip machine (regular)'
    )
    """Time to load a batch of regular slides into a coverslip machine."""

    coverslip_regular: DistributionInfo = pyd.Field(title='Coverslipping (regular)')
    """Time to affix coverslips to a batch of regular slides."""

    coverslip_megas: DistributionInfo = pyd.Field(title='Coverslipping (megas)')
    """Time to affix a coverslip to a single mega slide (manual task)."""

    unload_coverslip_machine_regular: DistributionInfo = pyd.Field(
        title='Unload coverslip machine (regular)'
    )
    """Time to unload a batch of regular slides into a coverslip machine."""

    labelling: DistributionInfo = pyd.Field(title='Labelling')
    """Time to label a slide."""

    load_scanning_machine_regular: DistributionInfo = pyd.Field(
        title='Load scanning machine (regular)'
    )
    """Time to load a batch of regular slides into a scanning machine."""

    load_scanning_machine_megas: DistributionInfo = pyd.Field(title='Load scanning machine (megas)')
    """Time to load a batch of mega slides into a scanning machine. There are dedicated scanning
    machines for mega slides."""

    scanning_regular: DistributionInfo = pyd.Field(title='Scanning (regular)')
    """Time to scan a batch of regular slides."""

    scanning_megas: DistributionInfo = pyd.Field(title='Scanning (megas)')
    """Time to scan a batch of mega slides."""

    unload_scanning_machine_regular: DistributionInfo = pyd.Field(
        title='Unload scanning machine (regular)'
    )
    """Time to unload a batch of regular slides from a scanning machine."""

    unload_scanning_machine_megas: DistributionInfo = pyd.Field(
        title='Unload scanning machine (megas)'
    )
    """Time to unload a batch of mega slides from a scanning machine."""

    block_and_quality_check: DistributionInfo = pyd.Field(title='Block and quality check')
    """Time to perform the block and quality checks for a specimen."""

    assign_histopathologist: DistributionInfo = pyd.Field(title='Assign histopathologist')
    """Time to assign a histopathologist to a specimen."""

    write_report: DistributionInfo = pyd.Field(title='Write histopathological report')
    """Time to write the histopathological report for a specimen."""

    @classmethod
    def from_workbook(cls, wbook: Workbook) -> Self:
        """Construct a dataclass instance from an Excel workbook."""
        tasks_df = pd.DataFrame(
            (table := get_table(wbook, 'Task Durations', 'TaskDurations'))[1:],
            columns=table[0]
        ).set_index('Task')
        return cls.model_validate({
            key: DistributionInfo(
                type=tasks_df.loc[field.title, 'Distribution'],
                low=tasks_df.loc[field.title, 'Optimistic'],
                mode=tasks_df.loc[field.title, 'Most Likely'],
                high=tasks_df.loc[field.title, 'Pessimistic'],
                time_unit=tasks_df.loc[field.title, 'Units'],
            )
            for key, field in TaskDurationsInfo.model_fields.items()
        })


# BATCH SIZES
class BatchSizes(pyd.BaseModel):
    """Information for tracking batch sizes in a model.  This is the number of
    specimens, blocks, or slides in a machine or delivery batch.  Batches in the model
    are homogeneous, i.e. all items in a batch are of the same type.

    The field titles in this class MUST match the rows of the Excel input file
    ("Batch Sizes" tab)."""

    deliver_reception_to_cut_up: pyd.PositiveInt = pyd.Field(title='Delivery (reception to cut-up)')
    """Delivery batch size, reception to cut-up (specimens)."""

    deliver_cut_up_to_processing: pyd.PositiveInt = pyd.Field(
        title='Delivery (cut-up to processing)'
    )
    """Delivery batch size, cut-up to processing (specimens)."""

    deliver_processing_to_microtomy: pyd.PositiveInt = pyd.Field(
        title='Delivery (processing to microtomy)'
    )
    """Delivery batch size, processing to microtomy (specimens)."""

    deliver_microtomy_to_staining: pyd.PositiveInt = pyd.Field(
        title='Delivery (microtomy to staining)'
    )
    """Delivery batch size, microtomy to staining (specimens)."""

    deliver_staining_to_labelling: pyd.PositiveInt = pyd.Field(
        title='Delivery (staining to labelling)'
    )
    """Delivery batch size, staining to labelling (specimens)."""

    deliver_labelling_to_scanning: pyd.PositiveInt = pyd.Field(
        title='Delivery (labelling to scanning)'
    )
    """Delivery batch size, labelling to scanning (specimens)."""

    deliver_scanning_to_qc: pyd.PositiveInt = pyd.Field(title='Delivery (scanning to QC)')
    """Delivery batch size, scanning to QC (specimens)."""

    bone_station: pyd.PositiveInt = pyd.Field(title='Bone station (blocks)')
    """Bone station (machine) batch size (blocks)."""

    processing_regular: pyd.PositiveInt = pyd.Field(title='Processing machine (regular blocks)')
    """Processing machine batch size, regular blocks."""

    processing_megas: pyd.PositiveInt = pyd.Field(title='Processing machine (mega blocks)')
    """Processing machine batch size, mega blocks."""

    staining_regular: pyd.PositiveInt = pyd.Field(title='Staining (regular slides)')
    """Staining machine batch size, regular slides."""

    staining_megas: pyd.PositiveInt = pyd.Field(title='Staining (mega slides)')
    """Staining machine batch size, mega slides."""

    digital_scanning_regular: pyd.PositiveInt = pyd.Field(title='Scanning (regular slides)')
    """Scanning machine batch size, regular slides."""

    digital_scanning_megas: pyd.PositiveInt = pyd.Field(title='Scanning (mega slides)')
    """Scanning machine batch size, mega slides."""

    @classmethod
    def from_workbook(cls, wbook: Workbook) -> Self:
        """Construct a dataclass instance from an Excel workbook."""
        batch_sizes_df = pd.DataFrame(
            (table := get_table(wbook, 'Batch Sizes', 'BatchSizes'))[1:],
            columns=table[0]
        ).set_index('Batch Name')
        return cls.model_validate({
            key: batch_sizes_df.loc[field.title, 'Size']
            for key, field in BatchSizes.model_fields.items()
        })


# RUNNER TIMES
class RunnerTimesConfig(pyd.BaseModel):
    """Configuration dataclass containing runner times between process stages."""

    reception_cutup: pyd.NonNegativeFloat = pyd.Field(
        validation_alias=pyd.AliasChoices('(reception, cutup)', 'reception_cutup'),
        title='Runner time, reception to cut-up'
    )
    """Runner time from the Reception stage to the Cut-Up stage."""

    cutup_processing: pyd.NonNegativeFloat = pyd.Field(
        validation_alias=pyd.AliasChoices('(cutup, processing)', 'cutup_processing'),
        title='Runner time, cut-up to processing'
    )
    """Runner time from the Cut-Up stage to the Processing stage."""

    processing_microtomy: pyd.NonNegativeFloat = pyd.Field(
        validation_alias=pyd.AliasChoices('(processing, microtomy)', 'processing_microtomy'),
        title='Runner time, processing to microtomy'
    )
    """Runner time from the Processing stage to the Microtomy stage."""

    microtomy_staining: pyd.NonNegativeFloat = pyd.Field(
        validation_alias=pyd.AliasChoices('(microtomy, staining)', 'microtomy_staining'),
        title='Runner time, microtomy to staining'
    )
    """Runner time from the Microtomy stage to the Staining stage."""

    staining_labelling: pyd.NonNegativeFloat = pyd.Field(
        validation_alias=pyd.AliasChoices('(staining, labelling)', 'staining_labelling'),
        title='Runner time, staining to labelling'
    )
    """Runner time from the Staining stage to the Labelling stage."""

    labelling_scanning: pyd.NonNegativeFloat = pyd.Field(
        validation_alias=pyd.AliasChoices('(labelling, scanning)', 'labelling_scanning'),
        title='Runner time, labelling to scanning',
    )
    """Runner time from the Labelling stage to the Scanning stage."""

    scanning_qc: pyd.NonNegativeFloat = pyd.Field(
        validation_alias=pyd.AliasChoices('(scanning, qc)', 'scanning_qc'),
        title='Runner time, scanning to QC'
    )
    """Runner time from the Scanning stage to the Block & Quality Check stage."""

    extra_loading: pyd.NonNegativeFloat = pyd.Field(title='Loading time')
    """Time to load a delivery batch."""

    extra_unloading: pyd.NonNegativeFloat = pyd.Field(title='Unloading time')
    """Time to unload a delivery batch."""

    @classmethod
    def from_workbook(cls, wbook: Workbook, speed: float | None = None) -> Self:
        """Construct a dataclass instance from an Excel workbook."""
        if speed is None:
            speed = get_name(wbook, 'runnerSpeed')
        df = pd.DataFrame(
            (table := get_table(wbook, 'Runner Times output', 'tableRunnerDistances'))[1:],
            columns=table[0]
        ).set_index('runner_journey')

        times = dict(df.to_records())
        return cls(
            **times,
            extra_loading=get_name(wbook, 'runnerLoadingTime'),
            extra_unloading=get_name(wbook, 'runnerUnloadingTime'),
        )


# GLOBAL VARIABLES
class Globals(pyd.BaseModel):
    """Stores the global variables of a model.

    Field titles should match the corresponding named range in the Excel input file
    and therefore should not contain any spaces or symbols."""

    prob_internal: Probability = pyd.Field(title='ProbInternal')
    """Probability that a specimen comes from an internal source, i.e. one that uses the EPIC
    system."""

    prob_urgent_cancer: Probability = pyd.Field(title='ProbUrgentCancer')
    """Probability that a cancer-pathway specimen has Urgent priority."""

    prob_urgent_non_cancer: Probability = pyd.Field(title='ProbUrgentNonCancer')
    """Probability that a non-cancer-pathway specimen has Urgent priority."""

    prob_priority_cancer: Probability = pyd.Field(title='ProbPriorityCancer')
    """Probability that a cancer-pathway specimen has Priority priority."""

    prob_priority_non_cancer: Probability = pyd.Field(title='ProbPriorityNonCancer')
    """Probability that a non-cancer-pathway specimen has Priority priority."""

    prob_prebook: Probability = pyd.Field(title='ProbPrebook')
    """Probability that a specimen requires pre-booking-in investigation."""

    prob_invest_easy: Probability = pyd.Field(title='ProbInvestEasy')
    """Probability that an internal specimen requires booking-in investigation, and the
    investigation is classified as "easy"."""

    prob_invest_hard: Probability = pyd.Field(title='ProbInvestHard')
    """Probability that an internal specimen requires booking-in investigation,  and the
    investigation is classified as "hard"."""

    prob_invest_external: Probability = pyd.Field(title='ProbInvestExternal')
    """Probability that an external specimen requires booking-in investigation."""

    prob_bms_cutup: Probability = pyd.Field(title='ProbBMSCutup')
    """Probability that a non-urgent specimen goes to BMS cut-up."""

    prob_bms_cutup_urgent: Probability = pyd.Field(title='ProbBMSCutupUrgent')
    """Probability that an urgent specimen goes to BMS cut-up."""

    prob_large_cutup: Probability = pyd.Field(title='ProbLargeCutup')
    """Probability that a non-urgent specimen goes to large specimens cut-up."""

    prob_large_cutup_urgent: Probability = pyd.Field(title='ProbLargeCutupUrgent')
    """Probability that an urgent specimen goes to large specimens cut-up."""

    prob_pool_cutup: Probability = pyd.Field(title='ProbPoolCutup')
    """Probability that a non-urgent specimen goes to Pool cut-up."""

    prob_pool_cutup_urgent: Probability = pyd.Field(title='ProbPoolCutupUrgent')
    """Probability that an urgent specimen goes to Pool cut-up."""

    prob_mega_blocks: Probability = pyd.Field(title='ProbMegaBlocks')
    """Probability that a large specimen cut-up produces mega blocks. With the remaining
    probability, large surgical blocks are produced instead."""

    prob_decalc_bone: Probability = pyd.Field(title='ProbDecalcBone')
    """Probability that an specimen requires decalcification at a bone station."""

    prob_decalc_oven: Probability = pyd.Field(title='ProbDecalcOven')
    """Probability that an specimen requires decalcification in a decalc oven."""

    prob_microtomy_levels: Probability = pyd.Field(title='ProbMicrotomyLevels')
    """Probability that a small surgical block produces a "levels" microtomy task. With remaining
    probability, a "serials" microtomy task is produced."""

    num_blocks_large_surgical: IntDistributionInfo = pyd.Field(title='NumBlocksLargeSurgical')
    """Parameters for the number of large surgical blocks produced in a cut-up that produces such
    blocks."""

    num_blocks_mega: IntDistributionInfo = pyd.Field(title='NumBlocksMega')
    """Parameters for the number of mega blocks produced in a cut-up that produces such blocks."""

    num_slides_larges: IntDistributionInfo = pyd.Field(title='NumSlidesLarges')
    """Parameters for the number of slides produced for a large surgical microtomy task."""

    num_slides_levels: IntDistributionInfo = pyd.Field(title='NumSlidesLarges')
    """Parameters for the number of slides produced for a levels microtomy task."""

    num_slides_megas: IntDistributionInfo = pyd.Field(title='NumSlidesLarges')
    """Parameters for the number of slides produced for a megas microtomy task."""

    num_slides_serials: IntDistributionInfo = pyd.Field(title='NumSlidesLarges')
    """Parameters for the number of slides produced for a serials microtomy task."""

    @classmethod
    def from_workbook(cls, wbook: Workbook) -> Self:
        """Construct a dataclass instance from an Excel workbook."""
        globals_floats = {
            key: get_name(wbook, field.title) for key, field in Globals.model_fields.items()
            if field.annotation == float
        }
        globals_dists = {
            key: IntDistributionInfo(
                type=get_name(wbook, field.title)[0][0],
                low=get_name(wbook, field.title)[0][1],
                mode=get_name(wbook, field.title)[0][2],
                high=get_name(wbook, field.title)[0][3]
            )
            for key, field in Globals.model_fields.items()
            if field.annotation == IntDistributionInfo
        }
        return cls(**globals_floats, **globals_dists)
