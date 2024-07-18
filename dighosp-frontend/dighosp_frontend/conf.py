"""Shared definitions for the front-end app."""
import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

env_get = os.environ.get

# If not Docker, load environment variables manually
if not os.path.isfile('/.dockerenv'):
    env_path = find_dotenv('.env', True)
    load_dotenv(env_path)
    ASSETS_DIRNAME = Path(env_path).parent.joinpath(env_get('ASSETS_DIRNAME')).resolve()
else:
    ASSETS_DIRNAME = env_get('ASSETS_DIRNAME', '/app/assets')


DES_FASTAPI_URL = env_get('DES_FASTAPI_URL', 'http://localhost/api/des')

if __name__ == "__main__":
    print(ASSETS_DIRNAME)
    print(ASSETS_DIRNAME.is_dir())
