import os
import redis
from rq import Worker, Queue
from app.jobs import send_due_reminder

# Connect to Redis
redis_connection = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))

# Create a worker
if __name__ == '__main__':
    worker = Worker([Queue(connection=redis_connection)], connection=redis_connection)
    worker.work()
