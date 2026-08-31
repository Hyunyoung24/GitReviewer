import os
import datetime
import anthropic
from dotenv import load_dotenv
from github import Github, Auth
from app.database import SessionLocal
from app.models import Repository, Review, ReviewComment

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


def review_pr(repo_name: str, pr_number: int, prompt_style: str = "general", max_tokens: int = 4096):
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

        # tool use(함수 호출)로 구조화된 출력을 강제
        # 이전에는 "JSON으로만 답해줘" 프롬프트 + json.loads로 직접 파싱했는데
        # diff에 백슬래시(윈도우 경로, 정규식 등)가 섞여 있으면 Claude가 이스케이프를
        # 빠뜨려서 json.loads가 "Invalid \escape" 오류로 죽는 문제가 있었음
        # tool_choice로 도구 호출을 강제하면 Anthropic 쪽에서 JSON을 직접 파싱해
        # message.content의 tool_use.input으로 넘겨주기 때문에 이 문제가 원천적으로 사라짐
        review_tool = {
            "name": "submit_review",
            "description": "코드 리뷰 결과를 제출합니다.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "summary": {
                        "type": "string",
                        "description": "전체 리뷰 요약, 마크다운 형식 (한국어, 3-5문장, '## 코드 리뷰'로 시작)"
                    },
                    "comments": {
                        "type": "array",
                        "maxItems": 3,
                        "description": "라인별 코멘트, 최대 3개. diff에서 +로 시작하는 줄만 line으로 지정",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string", "description": "파일 경로"},
                                "line": {"type": "integer", "description": "변경된 줄 번호"},
                                "body": {"type": "string", "description": "해당 줄에 대한 코멘트 (한국어)"},
                                "category": {"type": "string", "enum": ["bug", "style", "performance", "security"]},
                                "severity": {"type": "string", "enum": ["info", "caution", "warning"]}
                            },
                            "required": ["path", "line", "body", "category", "severity"]
                        }
                    }
                },
                "required": ["summary", "comments"]
            }
        }

        # 프롬프트 스타일별 추가 지시사항
        style_instructions = {
            "general": "전반적인 코드 품질, 버그, 개선점을 균형있게 리뷰해주세요.",
            "security": "보안 취약점과 잠재적 위험에 집중해서 리뷰해주세요. XSS, SQL Injection, 인증/인가 문제 등을 중점적으로 확인해주세요.",
            "performance": "성능 최적화 관점에서 리뷰해주세요. 불필요한 연산, 메모리 낭비, 느린 알고리즘 등을 중점적으로 확인해주세요.",
            "beginner": "초보자가 이해하기 쉽게 친절하게 설명해주세요. 전문 용어는 쉽게 풀어서 설명하고, 개선 방법도 구체적인 예시와 함께 알려주세요."
        }

        instruction = style_instructions.get(prompt_style, style_instructions["general"])

        # Claude Sonnet 4.6 모델 호출, 최대 4096토큰 제한
        # 한 번만 질문하고 답변을 받는 구조이기 때문에 assistant 없이 user만 할당
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            tools=[review_tool],
            tool_choice={"type": "tool", "name": "submit_review"},
            messages=[
                {
                    "role": "user",
                    "content": f"""오늘 날짜는 {datetime.date.today()}입니다.
아래 코드 변경사항을 리뷰하고, submit_review 도구를 호출해서 결과를 제출해주세요.

리뷰 방향: {instruction}

{diff_text}"""
                }
            ]
        )

        # tool_choice로 강제했으므로 content에는 tool_use 블록이 반드시 존재
        # input은 Anthropic이 이미 파싱한 dict라 json.loads가 필요 없음
        tool_use_block = next(b for b in message.content if b.type == "tool_use")
        review_data = tool_use_block.input
        print(f"Claude 응답 (tool_use): {str(review_data)[:100]}...")

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
                    category = c.get("category", "general"), 
                    severity = c.get("severity", "info")
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