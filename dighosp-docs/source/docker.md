# Docker and Docker Compose

:::{note}
We will migrate all services to Kubernetes in the future, using the [Helm](https://helm.sh/docs/) orchestrator.
:::

Currently, we use Docker Compose to launch the services of the Digital Hospitals platform. The main Docker Compose file contains one `include` directive for each project module, as well as `services`, `volume`, and `secret` sections for defining shared services such as MongoDB. The use of the `include` directive means that each module is responsible for defining its own Docker services.

Additionally, serviced mentioned in an `include` directive can have their behaviour modified using a `compose.override.yml` file. This is mostly useful for overriding port mappings and environment variables so that a module can run in both standalone mode or integrated into the full Digital Hospitals platform infrastructure.
