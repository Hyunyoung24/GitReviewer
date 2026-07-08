import os
import datetime
import json
import anthropic
from dotenv import load_dotenv
from github import Github, Auth
from app.database import SessionLocal
from app.models import Repository, Review, ReviewComment

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

    db = SessionLocal()

    # 같은 저장소로 들어온 리뷰들 묶어서 처리
    try:
        # repo_name은 "소유자/리포지토리명" 형식
        # 슬래시(/)를 기준으로 분할해 앞은 owner, 뒤는 repo_name_only
        owner, repo_name_only = repo_name.split("/")
        
        # 테이블 Repository를 찾고, 없으면 생성
        db_repo = db.query(Repository).filter(
            Repository.owner == owner,
            Repository.name == repo_name_only
        ).first()

        if not db_repo:
            db_repo = Repository(owner = owner, name = repo_name_only)
            db.add(db_repo)
            # 커밋 전에 임시로 DB에 반영
            # db_repo.id를 확보해서 Review에 repo_id로 넣는 용도
            db.flush()

        # SHA, PR 번호로 중복인지 체크
        existing_review = db.query(Review).filter(
            Review.commit_sha == pr.head.sha,
            Review.pr_number == pr_number
        ).first()

        if existing_review:
            print(f"이미 리뷰된 커밋 (SHA: {pr.head.sha[:7]}) - 건너뜀")
            return
        
        # diff 가져오기
        files = pr.get_files()
        diff_text = ""
        # PR에서 변경된 파일들을 돌면서 파일명과 변경 내역을 텍스트로 연결
        for f in files:
            diff_text += f"파일: {f.filename}\n"
            diff_text += f"{f.patch}\n"

        print(f"diff: {diff_text[:100]}...")

        # Claude 리뷰 요청
        # .env의 ANTHROPIC_API_KEY로 인증
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        # Claude Sonnet 4.6 모델 호출, 최대 3000토큰 제한 (답변이 너무 짧으면 늘리기)
        # 한 번만 질문하고 답변을 받는 구조이기 때문에 assistant 없이 user만 할당
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=3000,
            messages=[
                {
                    "role": "user",
                    "content": f"""오늘 날짜는 {datetime.date.today()}입니다.
아래 코드 변경사항을 리뷰해주세요.
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트는 절대 포함하지 마세요.
{{
    "summary": "## 코드 리뷰\n\n전체 리뷰 요약을 마크다운 형식으로 작성 (한국어, 3-5문장)",
    "comments": [
        {{
            "path": "파일 경로",
            "line": 변경된 줄 번호 (숫자),
            "body": "해당 줄에 대한 코멘트 (한국어)"
        }}
    ]
}}

comments는 최대 3개까지만 작성하세요.
diff에서 + 로 시작하는 줄만 line으로 지정하세요.

{diff_text}"""
                }
            ]
        )

        # Claude API는 content를 리스트 형태로 반환
        # [{"type: "text", "text": "" 코드 리뷰\n..."}] 구조
        # content[0]으로 첫 번째 요소, 그 중에서 텍스트만 가져오기
        raw_response = message.content[0].text
        print(f"Claude 응답: {raw_response[:100]}...")

        # JSON 파싱, 마크다운 감싸기 제거
        clean_response = raw_response.strip().removeprefix("```json").removesuffix("```").strip()
        review_data = json.loads(clean_response)
        summary = review_data.get("summary", "")
        comments = review_data.get("comments", [])

        print(f"요약: {summary[:50]}...")
        print(f"라인 코멘트 수: {len(comments)}개")

        db_review = Review(
            repo_id = db_repo.id, 
            pr_number = pr_number, 
            title = pr.title, 
            status = "completed", 
            summary = summary, 
            commit_sha = pr.head.sha 
        )    
        db.add(db_review)
        db.flush()

        # PR에 댓글 달기
        pr.create_issue_comment(summary)
        commit = repo.get_commit(pr.head.sha)
        
        for c in comments:
            try:
                pr.create_review_comment(
                    body = c["body"], 
                    commit = commit, 
                    path = c["path"], 
                    line = c["line"]
                )
                # 라인 코멘트를 DB에도 저장
                db_comment = ReviewComment(
                    review_id = db_review.id, 
                    file_path = c["path"], 
                    line_number = c["line"], 
                    body = c["body"], 
                    category = "general", 
                    severity = "info"
                )
                db.add(db_comment)
                print(f"라인 코멘트 작성 완료: {c['path']} {c['line']}번째 줄")
            except Exception as e:
                print(f"라인 코멘트 오류 ({c['path']} {c['line']}번째 줄): {e}")

        # 커밋
        db.commit()
        print(f"DB 저장 완료 - 리뷰 ID: {db_review.id}")
        print("PR 코멘트 작성 완료")
    
    # 오류 발생시 이번 트랜잭션 전체를 취소하고 롤백
    except Exception as e:
        db.rollback()
        print(f"DB 저장 오류: {e}")

    # 성공/실패 여부와 상관없이 항상 DB 연결 해제
    finally:
        db.close()