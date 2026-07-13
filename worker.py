import os
from dotenv import load_dotenv
from redis import Redis
from rq import Worker, Queue
from rq.worker import SimpleWorker

load_dotenv(override=False)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

if __name__ == "__main__":
    redis_conn = Redis.from_url(REDIS_URL)
    queues = [Queue(connection=redis_conn)]
    worker = SimpleWorker(queues=queues, connection=redis_conn)
    worker.work()