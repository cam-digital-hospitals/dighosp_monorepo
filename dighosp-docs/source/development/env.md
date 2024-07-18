# .env file usage

When hosting services in Docker, we use the `environment` directive in `compose.yml` or `compose.override.yml` to set environment variables for the Docker container. This is not available for Python scripts run on the host machine. Instead, we use an `.env` file to set environment variables instead:

```{code} bash
### .env ###

MONGO_URL_PUBLIC=localhost
MONGO_PORT_PUBLIC=27017

REDIS_URL_PUBLIC=localhost
REDIS_PORT_PUBLIC=6379
```

```{code} python
### conf.py ###

from dotenv import find_dotenv, load_dotenv

env_get = os.environ.get

# If not Docker, load environment variables manually
if not os.path.isfile('/.dockerenv'):
    load_dotenv(find_dotenv('.env', True))

# The rest of the file loads environment variables into Python, regardless of their source
```

See the [Docker documentation](https://docs.docker.com/compose/environment-variables/envvars-precedence/) on the precedence rules regarding environment variables.
