import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
from redis import Redis
from rq import Worker, Queue
from rq.worker import SimpleWorker

load_dotenv(override=False)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
    def log_message(self, format, *args):
        pass

def run_health_server():
    server = HTTPServer(('0.0.0.0', 8001), HealthHandler)
    server.serve_forever()

# 헬스체크 서버 백그라운드 실행
if __name__ == "__main__":
    threading.Thread(target=run_health_server, daemon=True).start()

    redis_conn = Redis.from_url(REDIS_URL)
    queues = [Queue(connection=redis_conn)]
    worker = SimpleWorker(queues=queues, connection=redis_conn)
    worker.work()