"""Shared definitions for the front-end app."""
import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

env_get = os.environ.get

# If not Docker, load environment variables manually
#
# ASSETS_DIRNAME is relative to the .env file if non-Docker and absolute if Docker
if not os.path.isfile('/.dockerenv'):
    env_path = find_dotenv('.env', True)
    load_dotenv(env_path)
    ASSETS_DIRNAME = Path(env_path).parent.joinpath(env_get('ASSETS_DIRNAME')).resolve()
else:
    ASSETS_DIRNAME = env_get('ASSETS_DIRNAME', '/app/assets')


DES_FASTAPI_URL = env_get('DES_FASTAPI_URL', 'http://localhost/api/des')
BASE_PATH = env_get('DASH_BASE_PATHNAME', '/')

if __name__ == "__main__":
    print(ASSETS_DIRNAME)
    print(ASSETS_DIRNAME.is_dir())
