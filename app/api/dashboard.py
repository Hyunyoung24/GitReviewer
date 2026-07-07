from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Repository, Review
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard_page", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html"
    )

@router.get("/dashboard")
def get_dashboard(db: Session = Depends(get_db)):
    # 최근 리뷰 10개를 최신순으로 가져오기
    reviews = db.query(Review).order_by(Review.created_at.desc()).limit(10).all()
    
    result = []
    for review in reviews:
        # 리뷰에 연결된 저장소 정보를 따로 조회
        repo = db.query(Repository).filter(Repository.id == review.repo_id).first()
        result.append({
            "id": review.id,
            # 저장소가 없으면 unknown으로 표시
            "repo": f"{repo.owner}/{repo.name}" if repo else "unknown",
            "pr_number": review.pr_number,
            "title": review.title,
            "status": review.status,
            # datetime을 JSON으로 직렬화할 수 있게 문자열로 변환
            "created_at": review.created_at.isoformat() if review.created_at else None,
        })
    
    return {"reviews": result}