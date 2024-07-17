"""Configuration settings for the DES module.

Environment variables are defined in .env, which is automatically loaded by Poetry if
the poetry-dotenv-plugin is installed (base environment) or by Docker Compose.
"""

import os
import pathlib

from dotenv import find_dotenv, load_dotenv

env_get = os.environ.get

# If not Docker, load environment variables manually
if not os.path.isfile('/.dockerenv'):
    load_dotenv(find_dotenv('.env', True))

MONGO_URL = env_get('MONGO_URL', env_get('MONGO_URL_PUBLIC'))
MONGO_PORT = int(env_get('MONGO_PORT', env_get('MONGO_PORT_PUBLIC')))
MONGO_USER = env_get('MONGO_USER', 'root')

path = pathlib.Path(os.path.dirname(__file__)) / '../../secrets/mongo-root-pw.txt'
MONGO_PASSWORD_FILE = env_get('MONGO_PASSWORD_FILE', path.resolve())

with open(MONGO_PASSWORD_FILE, 'r', encoding='utf-8') as fp:
    MONGO_PASSWORD = fp.read()

MONGO_TIMEOUT_MS = 5000

REDIS_URL = env_get('REDIS_URL', env_get('REDIS_URL_PUBLIC'))
REDIS_PORT = int(env_get('REDIS_PORT', env_get('REDIS_PORT_PUBLIC')))
