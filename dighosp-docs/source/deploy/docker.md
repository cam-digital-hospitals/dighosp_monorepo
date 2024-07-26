# Docker and Docker Compose

Currently, we use Docker Compose to launch the services of the Digital Hospitals platform. The main Docker Compose file contains one `include` directive for each project module, as well as `services`, `volume`, and `secret` sections for defining shared services such as MongoDB. The use of the `include` directive means that each module is responsible for defining its own Docker services.

Additionally, serviced mentioned in an `include` directive can have their behaviour modified using a `compose.override.yml` file. This is mostly useful for overriding port mappings and environment variables so that a module can run in both standalone mode or integrated into the full Digital Hospitals platform infrastructure.

## Docker bake

`docker buildx bake` is used to build the container images, both locally and using GitHub Actions. By default, this looks for a file called `docker-bake.hcl` in the root directory. For more information, see the [official documentation](https://docs.docker.com/build/bake/introduction/).

## Example workflow

While developing, we work on the `latest` tag:

```bash
# Useful bash functions and aliases
source scripts.sh

# While developing
bake && dev up -d
dev down

# The "prod up" command reduces the number of exposed ports so that all services
# are available via the webproxy only.
```

Pushing the project to the "main" branch will automatically rebuild the images defined in `docker-bake.hcl` and push them to `ghcr.io`, using GitHub Actions.

### Tagged Docker images

When we want to assign a version tag, e.g `0.1.1`:

```bash
source scripts.sh

# Update version numbers in pyproject.toml files
version-all 0.1.1

# Get latest versions from Github Container Registry
dpull

# Assign tags
dassign 0.1.1

# Test tagged deployment
# Set the TAG variable to be read by Docker Compose
TAG=0.1.1 prod up -d
TAG=0.1.1 prod down

# Push images
dpush-tag 0.1.1
```
