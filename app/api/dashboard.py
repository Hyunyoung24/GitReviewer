from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Repository, Review, ReviewComment
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
def get_dashboard(db: Session = Depends(get_db), page: int = 1, per_page: int = 10, repo: str = None):
    # 전체 리뷰 수 계산 (필터 적용)
    query = db.query(Review)
    if repo:
        owner, name = repo.split("/")
        db_repo = db.query(Repository).filter(
            Repository.owner == owner,
            Repository.name == name
        ).first()
        if db_repo:
            query = query.filter(Review.repo_id == db_repo.id)
        else:
            query = query.filter(False)

    total = query.count()
    offset = (page - 1) * per_page
    reviews = query.order_by(Review.created_at.desc()).offset(offset).limit(per_page).all()
    
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
            "summary": review.summary,
        })

    # 카테고리별 코멘트 개수 집계
    category_counts = (
        db.query(ReviewComment.category, func.count(ReviewComment.id))
        .group_by(ReviewComment.category)
        .all()
    )
    categories = { cat: count for cat, count in category_counts }

    # 전체 리뷰 기준 저장소별 집계 (차트용)
    all_reviews = db.query(Review).all()
    repo_counts = {}
    for r in all_reviews:
        repo = db.query(Repository).filter(Repository.id == r.repo_id).first()
        repo_name = f"{repo.owner}/{repo.name}" if repo else "unknown"
        repo_counts[repo_name] = repo_counts.get(repo_name, 0) + 1

    return {
        "reviews": result,
        "categories": categories,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
        "repo_counts": repo_counts
    }