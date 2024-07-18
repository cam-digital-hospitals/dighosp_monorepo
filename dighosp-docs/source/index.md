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
- Frontend server
- [DES (discrete event simulation)](project:./modules/des.md)
    - [API docs (Swagger)](/api/des/docs){.external}
- BIM (building information modelling)
- Asset status
- Staff scheduling
- Sensor feed

## Development

- <project:./development/prerequisites.md>
- **Code standards**
    - [Python (isort, autopep8, pylint)](project:./development/code_python.md)
    - Javascript/Typescript
    - TOML/YAML
- <project:./development/env.md>

## Deployment

- <project:./docker.md>
- Reverse proxy service

## <project:./roadmap.md>

## <project:./changelog.md>

:::{toctree}
:hidden:

🏠 Home <self>
:::

:::{toctree}
:hidden:
:caption: Modules

modules/overview
DES <modules/des>
:::

:::{toctree}
:hidden:
:caption: Development

development/prerequisites
development/code_python
development/env
:::

:::{toctree}
:hidden:
:caption: Deployment

docker
:::

:::{toctree}
:hidden:
:caption: Roadmap

roadmap
:::

:::{toctree}
:hidden:
:caption: Changelog

changelog
:::