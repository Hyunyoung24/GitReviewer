import os
import anthropic
from dotenv import load_dotenv
from github import Github, Auth

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

def review_pr(repo_name: str, pr_number: int):
    print(f"리뷰 시작: {repo_name} PR #{pr_number}")

    # GitHub 연결
    g = Github(auth=Auth.Token(GITHUB_TOKEN))
    repo = g.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    commit = repo.get_commit(pr.head.sha)

    # diff 가져오기
    files = pr.get_files()
    diff_text = ""
    for f in files:
        diff_text += f"파일: {f.filename}\n"
        diff_text += f"{f.patch}\n"

    print(f"diff: {diff_text[:100]}...")

    # Claude 리뷰 요청
    import datetime
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

    # PR에 댓글 달기
    pr.create_issue_comment(review_comment)
    print("PR 댓글 작성 완료")