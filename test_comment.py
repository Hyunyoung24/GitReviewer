import os
import datetime
from dotenv import load_dotenv
from github import Github, Auth
import anthropic

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
REPO_NAME = "Hyunyoung24/springboot-developer"
PR_NUMBER = 1

# GitHub 연결
# g = Github(GITHUB_TOKEN)
g = Github(auth=Auth.Token(GITHUB_TOKEN))
repo = g.get_repo(REPO_NAME)
pr = repo.get_pull(PR_NUMBER)
commit = repo.get_commit(pr.head.sha)

# PR diff 가져오기
files = pr.get_files()
diff_text = ""
for f in files:
    diff_text += f"파일: {f.filename}\n"
    diff_text += f"{f.patch}\n"

print(f"diff: {diff_text}")

# Claude에게 리뷰 요청
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
print(f"\nClaude 리뷰: {review_comment}")

# PR에 댓글 달기
pr.create_issue_comment(review_comment)
print("\nPR 댓글 작성 완료")