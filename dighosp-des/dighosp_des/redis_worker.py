"""A Redis worker for dev purposes. In production, we will use Kubernetes instead."""

import logging

from redis import Redis
from rq import Queue, Worker
from singleton_decorator import singleton

from .conf import REDIS_PORT, REDIS_URL

# Connect to Redis service, throws ConnectionError if service unavailable
redis = Redis(
    host=REDIS_URL,
    port=REDIS_PORT
)


@singleton
class RedisSingleton():
    def __init__(self) -> None:
        self.work_queue = Queue(name='default', connection=redis, default_timeout=3600)
        self.worker = Worker(['default'], connection=redis)


if __name__ == '__main__':
    print(f'{REDIS_URL}:{REDIS_PORT}')
    logger = logging.getLogger(__name__)
    logger.addHandler(logging.StreamHandler())
    rds = RedisSingleton()
    rds.worker.work()
