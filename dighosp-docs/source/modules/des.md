# Discrete-event Simulation module

The discrete-event simulation (DES) module takes a configuration file (.xlsx) as input and computes a set of key performance indicators (KPIs), using DES to predict the evolution of system state. The modelled system is the histopathology lab at Addenbrooke's Hospital, Cambridge, UK.

## Service architecture 

```{kroki}
:type: plantuml

@startuml

participant "Frontend" as User
participant "API server" as API
database DB
participant Orchestrator

User -> API: Simulation request
API -> DB: New simulation
DB --> API: OK

API --> User: 202 Accepted
API -> Orchestrator: Enqueue simulation replications

Orchestrator -> Worker : Job
activate Worker #77FF77

loop status check
User -> API: Simulation query
API -> DB: Fetch simulation status
DB --> API: Simulation status (running)
API --> User: Simulation status (running)
end

Worker --> DB: Result
Worker --> Orchestrator --: Job sucessful

==All workers completed==

Orchestrator -> Worker : Precompute\nfigure / table\ndata
activate Worker #77FF77
Worker --> DB: KPI figure / table data
Worker --> Orchestrator --: Job sucessful

User -> API: Simulation query
API -> DB: Fetch simulation status
DB --> API: Simulation status (finished)
API --> User: Simulation status (finished)

@enduml
```

Currently, the Orchestrator is based on [RQ](https://python-rq.org/docs/); a Kubernetes-based solution is planned (each task to generate a new worker pod, which is destroyed upon task completion).

Note that in the above figure, we precompute the KPI results to display. In fact, the stored objects in the database are entire [Plotly figures converted into `dict` form](https://plotly.com/python/creating-and-updating-figures/#converting-graph-objects-to-dictionaries-and-json). This greatly reduces page load time when viewing simulation results via the frontend service.

```{caution}
A major drawback of the above method is that updates to the KPIs displayed in the frontend may break compatibility with older simulation results.
```

## Simulation processes

Simulation processes are handled by defining `salabim.Component` instances and activating (`activate()`) their attached methods. By default, any `process()` method is automatically activated upon component instantiation.

Components based on physical entities in the simulation model include `Specimen`, `Block`, `Slide`, and `Batch`. Additionally, process components include `ArrivalGenerator`, `ResourceScheduler`, and `BaseProcess`.

### The BaseProcess class and derived classes

```{kroki}
:type: plantuml

@startuml

left to right direction

abstract BaseProcess {
    name: str
    env: Model
    in_queue: salabim.Store

    {abstract} process: () → None
}

class Process {
    in_type: type
    fn: Callable

    {static} new: (...) → None
}
BaseProcess <|-- Process

class BatchingProcess {
    batch_size: int | Distribution
    out_process: str

    {static} new: (...) → None
}
BaseProcess <|-- BatchingProcess

class CollationProcess {
    count_attr: str
    out_process: str
    - pool: dict[str, list]

    {static} new: (...) → None
}
BaseProcess <|-- CollationProcess

class DeliveryProcess {
    runner: salabim.Resource
    durations: RunnerDurations
    out_process: str

    {static} new: (...) → None
}
BaseProcess <|-- DeliveryProcess

@enduml
```

Each derived class contains a `new()` method with different parameters based on the process type. All `new()` methods adds the process object to the `processes` attribute of the simulation model/environment object `env`; additionally, the `Process` class also registers `fn` into the list of defined methods for the class specified by `in_type`. For example,
`Process.new(env, Specimen, task)`{l=python}
sets `env.processes['task']` to the newly created process, and also sets `Specimen.task` to the `task` method.

Note that the above works even for classes generated using templates, for example, the `Batch[Block]` class is used for many processes in the Processing stage of the simulation model.

## Specimen data, Monitors, and KPI calculation

A `Model.specimen_data` dict object is used to store data for all specimens, including timestamps for the start and end of each histopathology stage. The number of specimens in each stage is tracked using `salabim.Monitor` objects; additionally, we use the built-in monitors of the `salabim.Resource` class to monitor resource capacity and usage.

From the above, we compute KPIs such as overall and/or lab turnaround time and mean resource utilisation, and compare these across multiple simulation scenarios.
