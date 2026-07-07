import os
import datetime
import anthropic
from dotenv import load_dotenv
from github import Github, Auth
from app.database import SessionLocal
from app.models import Repository, Review

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

def review_pr(repo_name: str, pr_number: int):
    print(f"리뷰 시작: {repo_name} PR #{pr_number}")

    # GitHub 연결
    g = Github(auth=Auth.Token(GITHUB_TOKEN))
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
#    commit = repo.get_commit(pr.head.sha)

    # diff 가져오기
    files = pr.get_files()
    diff_text = ""
    for f in files:
        diff_text += f"파일: {f.filename}\n"
        diff_text += f"{f.patch}\n"

    print(f"diff: {diff_text[:100]}...")

    # Claude 리뷰 요청
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1000,
        messages=[
            {
                "role": "user",
                "content": f"""오늘 날짜는 {datetime.date.today()}입니다.
                            아래 코드 변경사항을 리뷰해주세요.
                            한 가지 개선점이나 주의사항을 짧게 한국어로 작성해주세요.

                            {diff_text}"""
            }
        ]
    )

    review_comment = message.content[0].text
    print(f"Claude 리뷰 완료: {review_comment[:50]}...")

    db = SessionLocal()

    # 같은 저장소로 들어온 리뷰들 묶어서 처리
    try:
        owner, repo_name_only = repo_name.split("/")
        
        # Repository를 찾고, 없으면 생성
        db_repo = db.query(Repository).filter(
            Repository.owner == owner,
            Repository.name == repo_name_only
        ).first()

        if not db_repo:
            db_repo = Repository(owner = owner, name = repo_name_only)
            db.add(db_repo)
            # commit 전에 db_repo.id 먼저 확보
            db.flush()

        db_review = Review(
            repo_id = db_repo.id, 
            pr_number = pr_number, 
            title = pr.title, 
            status = "completed", 
            summary = review_comment, 
            commit_sha = pr.head.sha 
        )

        db.add(db_review)
        db.commit()
        print(f"DB 저장 완료 - 리뷰 ID: {db_review.id}")
    
    # 오류 발생시 이번 트랜잭션 전체를 취소하고 롤백
    except Exception as e:
        db.rollback()
        print(f"DB 저장 오류: {e}")

    # 완료되면 자원 해제
    finally:
        db.close()

    # PR에 댓글 달기
    pr.create_issue_comment(review_comment)
    print("PR 댓글 작성 완료")