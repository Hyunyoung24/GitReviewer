from fastapi import FastAPI, Request, HTTPException
import hmac
import hashlib
import os
import asyncio
from dotenv import load_dotenv
from app.core.reviewer import review_pr

load_dotenv()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")

app = FastAPI()

def verify_signature(payload: bytes, signature: str) -> bool:
    if not WEBHOOK_SECRET:
        return True
    expected = "sha256=" + hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

async def run_review(repo_name: str, pr_number: int):
    try:
        await asyncio.get_event_loop().run_in_executor(
            None, review_pr, repo_name, pr_number
        )
    except Exception as e:
        print(f"오류: {e}")
        

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
            # 백그라운드로 리뷰 실행
            asyncio.create_task(run_review(repo_name, pr_number))
    
    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy"}