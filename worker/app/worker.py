import os
import time
from rq import Connection, Queue, Worker
from redis import Redis

redis_url = os.environ.get("REDIS_URL", "redis://redis:6379/0")

conn = Redis.from_url(redis_url)


if __name__ == "__main__":
    with Connection(conn):
        queue = Queue("default")
        worker = Worker([queue])
        worker.work()
