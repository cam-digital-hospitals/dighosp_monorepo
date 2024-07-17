"""Defines specimens, blocks, and slides."""

from abc import ABC, abstractmethod
from enum import IntEnum
from typing import TYPE_CHECKING, Optional

import salabim as sim

if TYPE_CHECKING:
    from .model import Model


class Priority(IntEnum):
    """Specimen priority. Lower value = higher priority."""
    ROUTINE = 0
    CANCER = -1
    PRIORITY = -2
    URGENT = -3


class Component(sim.Component, ABC):
    """A salabim component with additional fields."""
    env: 'Model'
    prio: Priority
    parent: Optional['Component']

    @abstractmethod  # Prevent direct instantiation of this class
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Specimen(Component):
    """A tissue specimen."""
    blocks: list['Block']

    def __init__(self, *args, **kwargs):  # Must override abstractmethod
        super().__init__(*args, **kwargs)

    def setup(self, **kwargs) -> None:
        self.env.specimen_data[self.name()] = kwargs
        self.blocks = []

        # Select: internal or external specimen
        self.env.specimen_data[self.name()]['source'] = sim.CumPdf(
            ('Internal', 'External'),
            cumprobabilities=(self.env.globals.prob_internal, 1),
            randomstream=self.env.rng,
            env=self.env
        ).sample()

        # Select: Priority
        dist = 'cancer' if kwargs.get('cancer', False) else 'non_cancer'
        self.prio = sim.CumPdf(
            (
                Priority.URGENT,
                Priority.PRIORITY,
                Priority.CANCER if dist == 'cancer' else Priority.ROUTINE
            ),
            cumprobabilities=(
                getattr(self.env.globals, f'prob_urgent_{dist}'),
                getattr(self.env.globals, f'prob_urgent_{dist}')
                + getattr(self.env.globals, f'prob_priority_{dist}'),
                1
            ),
            randomstream=self.env.rng,
            env=self.env
        ).sample()

    def process(self):
        """Insert specimen into the `arrive_reception` in-queue."""
        self.enter(self.env.processes['arrive_reception'].in_queue)

    def timestamp(self, name: str):
        """Save timestamp data to `self.env.specimen_data`."""
        self.env.specimen_data[self.name()][name] = self.env.now()


class Block(Component):
    """A wax block (or cassette to be turned into a wax block)."""
    slides: list['Slide']

    def __init__(self, *args, **kwargs):  # Must override abstractmethod
        super().__init__(*args, **kwargs)

    @property
    def prio(self):
        """Priority of the block, inherited from the parent specimen."""
        return self.parent.prio

    def setup(self, parent: Specimen, **kwargs) -> None:  # pylint: disable=arguments-differ
        self.parent: Specimen = parent
        self.slides = []
        self.data = kwargs


class Slide(Component):
    """A glass slide."""

    def __init__(self, *args, **kwargs):  # Must override abstractmethod
        super().__init__(*args, **kwargs)

    def setup(self, parent: Block, **kwargs) -> None:  # pylint: disable=arguments-differ
        self.parent: Block = parent
        self.data = kwargs


class Batch[Ty: Component](Component):
    """A batch of Component objects."""

    def __init__(self, *args, **kwargs):  # Must override abstractmethod
        super().__init__(*args, **kwargs)

    def setup(self, **kwargs) -> None:  # pylint: disable=arguments-differ
        self.data = kwargs
        self.items: list[Ty] = []
