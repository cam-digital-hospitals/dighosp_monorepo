# Digital Hospitals project

This website contains the internal documentation for the [Digital Hospitals project](/){.external} by the Institute for Manufacturing, the University of Cambridge.

## Modules

- [Overview](project:./modules/overview.md)
- <project:./modules/frontend.md>
- <project:./modules/webproxy.md>

### Backend services

- [DES (discrete event simulation)](project:./modules/des.md)
    - [🔗 API docs (Swagger)](/api/des/docs){.external}
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

- <project:./deploy/docker.md>
- <project:./deploy/proxy.md>

## <project:./roadmap.md>

## <project:./changelog.md>

<!-- Use hack to enable external relative link, see
https://github.com/sphinx-doc/sphinx/issues/701, https://stackoverflow.com/a/31820846 -->
:::{toctree}
:hidden:

🏠 Home <self>
🔗Frontend </#http://>
:::

:::{toctree}
:hidden:
:caption: Modules

modules/overview
modules/frontend
modules/webproxy
DES service <modules/des>
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

deploy/docker
deploy/proxy
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