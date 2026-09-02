from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib
import os
from dotenv import load_dotenv
from app.core.reviewer import review_pr
from redis import Redis
from rq import Queue
from app.api.dashboard import router as dashboard_router
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

load_dotenv()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

# 리뷰 설정용 전역 변수
review_config = {
    "prompt_style": "general",
    "max_tokens": 5000,
    "custom_prompt": ""
}

# 앰 초기화, 라우터/정적 파일/템플릿 설정
app = FastAPI()
app.include_router(dashboard_router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")
# Redis 연결 및 queue 초기화
redis_conn = Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))
q = Queue(connection=redis_conn)

def verify_signature(payload: bytes, signature: str) -> bool:
    # .env의 WEBHOOK_SECRET이 비어 있을 경우 서명 검증 생략
    if not WEBHOOK_SECRET:
        return True
    # WEBHOOK_SECRET으로 payload를 SHA256 해시화해서 서명 생성
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    # == 비교는 앞글자부터 하나씩 비교하다가 다른 글자를 만나면 false를 반환
    # 즉 응답 시간에 따라 몇 글자까지 맞았는지 추측 가능 (타이밍 공격)
    # 타이밍 공격 방지를 위해 hmac.compare_digest로 전체를 비교
    return hmac.compare_digest(expected, signature)

@app.post("/webhook")
async def github_webhook(request: Request):
    # 서명 검증
    signature = request.headers.get("X-Hub-Signature-256", "")
    payload = await request.body()
    
    if not verify_signature(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # 이벤트 파싱
    event = request.headers.get("X-GitHub-Event", "")
    data = await request.json()
    
    if event == "pull_request":
        action = data.get("action", "")
        if action in ["opened", "synchronize"]:
            pr_number = data["pull_request"]["number"]
            repo_name = data["repository"]["full_name"]
            print(f"PR #{pr_number} 감지됨: {repo_name}")
            # review_pr 함수를 Redis 큐에 등록해서 워커로 백그라운드 처리
            # 웹훅이 200 응답을 보내면 리뷰는 queue를 통해 비동기 실행
            # 응답 지연으로 인한 GitHub 웹훅 타임아웃 방지
            q.enqueue(review_pr, repo_name, pr_number,
                review_config["prompt_style"],
                review_config["max_tokens"],
                review_config.get("custom_prompt", ""))
    
    return {"status": "ok"}

@app.get("/config")
async def get_config():
    from app.core.reviewer import style_instructions
    return { 
        **review_config,
        "style_instructions": style_instructions
    }

@app.post("/config")
async def update_config(config: dict):
    review_config.update(config)
    print(f"설정 변경: {review_config}")
    return review_config

# 서버 상태 확인용 엔드포인트 (모니터링용)
@app.get("/health")
async def health():
    return {"status": "healthy"}