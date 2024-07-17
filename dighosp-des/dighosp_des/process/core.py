"""Common definitions for histopathology model processes."""

import itertools
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable

import salabim as sim

from ..specimens import Batch, Component, Priority, Specimen

if TYPE_CHECKING:
    from ..config import ArrivalSchedule, ResourceSchedule
    from ..model import Model


ARR_RATE_INTERVAL_HOURS = 1
"""Interval duration for which specimen arrival rates are defined in the simulation Config
object."""

RESOURCE_ALLOCATION_INTERVAL_HOURS = 0.5
"""Interval duration for which resource allocations are defined in the simulation Config object."""


class ArrivalGenerator(sim.Component):
    """Specimen arrival generator process."""

    env: 'Model'
    """The simulation model and environment."""

    iterator: itertools.cycle
    """Iterator yielding the arrival rate for each hourly period. Repeats weekly."""

    cls_args: dict[str, Any]
    """Arguments passed to the `Specimen` constructor."""

    def __init__(self, *args, schedule: 'ArrivalSchedule', env: 'Model', **kwargs) -> None:
        super().__init__(*args, **kwargs, env=env, rates=schedule.rates)

    def setup(self, *, rates: list[float], **kwargs) -> None:  # pylint: disable=arguments-differ
        self.iterator = itertools.cycle(rates)
        self.cls_args = kwargs

    def process(self) -> None:
        """The generator process. Creates a sub-generator for each interval (of length
        `ARR_RATE_INTERVAL_HOURS`) with the specified rate."""
        dur = self.env.hours(ARR_RATE_INTERVAL_HOURS)
        for rate in self.iterator:
            if rate > 0:
                sim.ComponentGenerator(
                    Specimen,
                    generator_name=f'{self.name()}_sub',
                    duration=dur,
                    iat=sim.Exponential(rate=rate, randomstream=self.env.rng, env=self.env)
                )
            self.hold(dur)


class ResourceScheduler(sim.Component):
    """Resource scheduler class. The resource level is set every
    `RESOURCE_ALLOCATION_INTERVAL_HOURS` hours, either to the hourly entry in the `ResourceSchedule`
    if the day entry is equal to 1, or 0 otherwise."""

    env: 'Model'
    """The simulation model and environment."""

    resource: sim.Resource
    """The resource to control the allocation of."""

    schedule: 'ResourceSchedule'
    """The resource allocation schedule."""

    def __init__(self, *args, resource: sim.Resource, schedule: 'ResourceSchedule', env: 'Model',
                 **kwargs) -> None:
        super().__init__(*args, **kwargs, env=env, resource=resource, schedule=schedule)

    def setup(self, *,  # pylint: disable=arguments-differ
              resource: sim.Resource, schedule: 'ResourceSchedule') -> None:
        self.resource = resource
        self.schedule = schedule

    def process(self) -> None:
        """Change the resource capacity based on the schedule. Capacities are given in 30-min
        intervals."""
        for day_flag in itertools.cycle(self.schedule.day_flags):
            if day_flag == 0:
                # Skip day
                self.resource.set_capacity(0)
                self.hold(self.env.days(1))
            else:
                # Set capacity for each interval in day
                for allocation in self.schedule.allocation:
                    if allocation != self.resource.capacity() or self.env.now() == 0:
                        self.resource.set_capacity(allocation)
                    self.hold(self.env.hours(RESOURCE_ALLOCATION_INTERVAL_HOURS))


class BaseProcess(sim.Component, ABC):
    """A process with an in-queue. Typically does work on Components
    arriving to the in-queue and pushes completed components to another
    process' in-queue."""

    env: 'Model'
    """The simulation model and environment."""

    in_queue: sim.Store
    """The in-queue of the process from which entities are taken."""

    def __init__(self, *args, env: 'Model', **kwargs) -> None:
        super().__init__(*args, **kwargs, env=env)

    def setup(self) -> None:
        self.in_queue = sim.Store(name=f'{self.name()}.in_queue', env=self.env)

    @abstractmethod
    def process(self) -> None:
        """Method called by the simulation upon process instantiation."""


class Process(BaseProcess):
    """A looped processed that takes one entity from its in-queue at a time
    and activates it. Injects the process' `fn` function into the class definition of
    the entity's type.

    For example, `Process(name='do_this', Specimen, do_this)` injects
    `Specimen.do_this = do_this` and calls it for every arriving `Specimen`.
    """

    in_type: type[Component]
    """The type of the entities to be processed."""

    fn: Callable[[Component], None]
    """The function to be applied to each new arrival to the process. The name of the
    function should match the name of the `Process` instance."""

    def __init__(self, *args, in_type: type[Component],
                 fn: Callable[[Component], None], env: 'Model', **kwargs) -> None:
        super().__init__(*args, in_type=in_type, fn=fn, env=env, **kwargs)

    def setup(  # pylint:disable=arguments-differ
            self, in_type: type[Component], fn: Callable[[Component], None]) -> None:
        super().setup()
        self.in_type = in_type
        setattr(self.in_type, self.name(), fn)  # method injection

    def process(self) -> None:
        while True:
            self.from_store(self.in_queue)
            entity: Component = self.from_store_item()
            entity.activate(process=self.name())

    @classmethod
    def new(cls, env: 'Model', in_type: type, fn: Callable[[Component], None]) -> None:
        """Register a new process to a simulation environment."""
        env.processes[fn.__name__] = cls(
            fn.__name__, in_type=in_type, fn=fn, env=env
        )


class BatchingProcess[Ty: Component](BaseProcess):
    """Takes `batch_size` entites from `in_queue` and inserts a single
    instance of `out_type` to `env.processes[out_process].in_queue`."""

    batch_size: int | sim.Distribution
    """The batch size or its distribution."""

    out_process: str
    """The name of the process receiving the reconstituted parent entity."""

    def __init__(self, *args, batch_size: int | sim.Distribution, out_process: str,
                 env: 'Model', **kwargs) -> None:
        super().__init__(*args, batch_size=batch_size, out_process=out_process, env=env, **kwargs)

    def setup(self,  # pylint:disable=arguments-differ
              batch_size: int | sim.Distribution, out_process: str) -> None:
        super().setup()
        self.batch_size = batch_size
        self.out_process = out_process

    def process(self) -> None:
        while True:
            batch_size = self.batch_size() if callable(self.batch_size) else self.batch_size
            batch = Batch[Ty](env=self.env)
            for _ in range(batch_size):
                # FUTURE: implement fail_duration support for partial batching
                self.from_store(self.in_queue)
                item: Ty = self.from_store_item()
                item.register(batch.items)
            batch.enter(self.env.processes[self.out_process].in_queue)

    @classmethod
    def new(cls, name: str, batch_size: int | sim.Distribution, out_process: str,
            env: 'Model') -> None:
        """Register a new batching process to a simulation environment."""
        env.processes[name] = cls(
            name=name,
            batch_size=batch_size,
            out_process=out_process,
            env=env
        )


class CollationProcess(BaseProcess):
    """Takes entities from `in_queue` and places them into a pool. Once all entities with the same
    parent are found (based on comparing with a count attribute), the parent is inserted into
    `env.processes[out_process].in_queue`.
    """

    count_attr: str
    """The name of the attribute in the parent entity defining the number of child entities."""

    out_process: str
    """The name of the process receiving the reconstituted parent entity."""

    pool: dict[str, list[Component]]
    """The pool of Components awaiting collation. Keys are the parent components' names."""

    def __init__(self, *args, count_attr: str, out_process: str, env: 'Model', **kwargs) -> None:
        super().__init__(*args, env=env, count_attr=count_attr, out_process=out_process, **kwargs)

    def setup(self,  # pylint: disable=arguments-differ
              count_attr: str, out_process: str) -> None:
        super().setup()
        self.count_attr = count_attr
        self.out_process = out_process
        self.pool = {}

    def process(self) -> None:
        while True:
            self.from_store(self.in_queue)
            item: Component = self.from_store_item()
            key = item.parent.name()

            # Assign the fetched item to the matching key, creating a new list entry in the pool
            # if necessary
            if key not in self.pool:
                self.pool[key] = []
            self.pool[key].append(item)

            # Check count_attr to see if we have all items in the group.
            # Note that we have a central data structure for specimen data, but not for
            # Block or Slide data.
            data = (
                self.env.specimen_data[key] if isinstance(item.parent, Specimen)
                else item.parent.data
            )
            if len(self.pool[key]) == data[self.count_attr]:
                item.parent.enter_sorted(
                    self.env.processes[self.out_process].in_queue,
                    priority=item.parent.prio
                )
                del self.pool[key]

    @classmethod
    def new(cls, name: str, count_attr: str, out_process: str, env: 'Model') -> None:
        """Register a new collation process to a simulation environment."""
        env.processes[name] = cls(
            name=name,
            count_attr=count_attr,
            out_process=out_process,
            env=env
        )


@dataclass
class RunnerDurations:
    """Runner durations for loading/unloading a delivery batch and travelling to/from the
    destination."""

    collect: float | sim.Distribution
    """Time for the runner to collect the delivery batch."""

    out: float | sim.Distribution
    """Outbound trip duration; time for the runner to travel from the source to the destination."""

    unload: float | sim.Distribution
    """Time for the runner to unload the delivery batch."""

    retur: float | sim.Distribution
    """Return trip duration; time for the runner to travel from the destination to the source."""


class DeliveryProcess(BaseProcess):
    """Takes entities/batches from the `in_queue` and places them
    in `env.processes[out_process].in_queue`, after some delay.
    A resource is required to move the entity/batch and requires
    time to travel between the locations associated with the two
    processes.  Batches are unbatched upon arrival.
    """

    runner: sim.Resource
    """The resource (staff type) responsible for the delivery."""

    durations: RunnerDurations
    """Durations for collecting/unloading the delivery batch and travelling to/from the
    destination."""

    out_process: str
    """The name of the process receiving the delivery."""

    def __init__(self, *args, runner: sim.Resource, durations: RunnerDurations, out_process: str,
                 env: 'Model', **kwargs) -> None:
        super().__init__(*args, env=env, runner=runner, durations=durations,
                         out_process=out_process, **kwargs)

    def setup(self,  # pylint: disable=arguments-differ
              runner: sim.Resource, durations: RunnerDurations, out_process: str) -> None:
        super().setup()
        self.runner = runner
        self.durations = durations
        self.out_process = out_process

    def process(self) -> None:
        out_queue = self.env.processes[self.out_process].in_queue

        while True:
            self.from_store(self.in_queue)
            entity: Component = self.from_store_item()
            delivery_prio = (entity.prio if not isinstance(entity, Batch) else Priority.ROUTINE)

            self.request((self.runner, 1, delivery_prio))

            # Runner: collect items and make delivery
            self.hold(self.durations.collect)
            self.hold(self.durations.out)

            # Runner: unload delivered items
            self.hold(self.durations.unload)
            if isinstance(entity, Batch):
                for item in entity.items:
                    item: Component
                    item.enter_sorted(out_queue, priority=item.prio)
            else:
                entity.enter_sorted(out_queue, priority=entity.prio)

            # Runner: return to origin station
            self.hold(self.durations.retur)
            self.release()

    @classmethod
    def new(cls, name: str, runner: sim.Resource, durations: RunnerDurations, out_process: str,
            env: 'Model') -> None:
        """Register a new delivery process to a simulation environment."""
        env.processes[name] = cls(
            name=name,
            runner=runner,
            durations=durations,
            out_process=out_process,
            env=env
        )
