"""Scanning processes."""

from typing import TYPE_CHECKING

from ..specimens import Batch, Slide, Specimen
from .core import BatchingProcess, CollationProcess, DeliveryProcess, Process, RunnerDurations

if TYPE_CHECKING:
    from ..model import Model


def register_processes(env: 'Model') -> None:
    """Register processes to the simulation environment."""
    Process.new(env, Specimen, scanning_start)
    Process.new(env, Batch[Slide], scanning_regular)
    Process.new(env, Batch[Slide], scanning_megas)
    Process.new(env, Specimen, post_scanning)

    # Scanning batches
    BatchingProcess[Slide].new(
        'batcher.scanning_regular',
        batch_size=env.batch_sizes.digital_scanning_regular,
        out_process='scanning_regular',
        env=env
    )
    BatchingProcess[Slide].new(
        'batcher.scanning_megas',
        batch_size=env.batch_sizes.digital_scanning_megas,
        out_process='scanning_megas',
        env=env
    )

    # Collation
    CollationProcess.new(
        'collate.scanning.slides',
        count_attr='num_slides',
        out_process='collate.scanning.blocks',
        env=env,
    )
    CollationProcess.new(
        'collate.scanning.blocks',
        count_attr='num_blocks',
        out_process='post_scanning',
        env=env
    )

    # Delivery
    BatchingProcess[Specimen].new(
        'batcher.scanning_to_qc',
        batch_size=env.batch_sizes.deliver_scanning_to_qc,
        out_process='scanning_to_qc',
        env=env
    )
    DeliveryProcess.new(
        'scanning_to_qc',
        runner=env.resources.scanning_staff,
        durations=RunnerDurations(
            env.runner_times.extra_loading,
            env.runner_times.scanning_qc,
            env.runner_times.extra_unloading,
            env.runner_times.scanning_qc  # FUTURE: different outbound and return times?
        ),
        out_process='qc',
        env=env
    )


def scanning_start(self: Specimen) -> None:
    """Entry point for scanning."""
    self.env.wips.in_scanning.value += 1
    self.timestamp('scanning_start')

    for block in self.blocks:
        for slide in block.slides:
            slide.enter(
                self.env.processes[
                    f'batcher.scanning_{'megas' if slide.data['slide_type'] == 'megas'
                                        else 'regular'}'
                ].in_queue
            )


def scanning_generic(self: Batch[Slide], is_mega: bool) -> None:
    """Generic process for slide scanning."""

    megas_or_regular = 'megas' if is_mega else 'regular'

    # LOAD
    self.request(
        self.env.resources.scanning_staff,
        getattr(self.env.resources, f'scanning_machine_{megas_or_regular}')
    )
    self.hold(getattr(self.env.task_durations, f'load_scanning_machine_{megas_or_regular}'))
    self.release(self.env.resources.scanning_staff)

    # SCAN
    self.hold(getattr(self.env.task_durations, f'scanning_{megas_or_regular}'))

    # UNLOAD
    self.request(self.env.resources.scanning_staff)
    self.hold(getattr(self.env.task_durations, f'unload_scanning_machine_{megas_or_regular}'))
    self.release()

    for slide in self.items:
        slide.enter(self.env.processes['collate.scanning.slides'].in_queue)


def scanning_regular(self: Batch[Slide]) -> None:
    """Scan a batch of regular slides."""
    return scanning_generic(self, False)


def scanning_megas(self: Batch[Slide]) -> None:
    """Scan a batch of mega slides."""
    return scanning_generic(self, True)


def post_scanning(self: Specimen) -> None:
    """Post-scanning tasks."""
    self.env.wips.in_scanning.value -= 1
    self.timestamp('scanning_end')
    self.enter_sorted(self.env.processes['batcher.scanning_to_qc'].in_queue, self.prio)
