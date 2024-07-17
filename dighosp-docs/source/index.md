# Digital Hospitals project

This website contains the internal documentation for the Digital Hospitals project by the Institute for Manufacturing, the University of Cambridge.

:::{admonition} Serving these docs
:class: tip

Executing
`cd dighosp-docs && docker compose build && docker compose up -d`{l=bash}
will build and serve these docs at `http://localhost:80`.
:::

## Modules

- [Overview](project:./modules/overview.md)
- DES (discrete event simulation)
    - [API docs (Swagger)](/api/des/docs){.external}
- BIM (building information modelling)
- Asset status
- Staff scheduling
- Sensor feed

## Development

- [](project:./development/prerequisites.md)
- Code standards
    - Python (isort, autopep8, pylint)
- .env file usage

## Deployment

- Docker
- K8s and Helm
- Reverse proxy service

:::{toctree}
:hidden:

🏠 Home <self>
:::

:::{toctree}
:hidden:
:caption: Modules

modules/overview
:::

:::{toctree}
:hidden:
:caption: Development

development/prerequisites
:::

:::{toctree}
:hidden:
:caption: Deployment

:::