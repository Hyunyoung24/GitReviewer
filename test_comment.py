import os
from dotenv import load_dotenv
from github import Github, Auth

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "Hyunyoung24/springboot-developer"
PR_NUMBER = 1

# g = Github(GITHUB_TOKEN)
g = Github(auth=Auth.Token(GITHUB_TOKEN))
repo = g.get_repo(REPO_NAME)
pr = repo.get_pull(PR_NUMBER)

# PR의 최신 커밋
commit = repo.get_commit(pr.head.sha)

# 라인 코멘트 달기
pr.create_review_comment(
    body="라인 코멘트 테스트용",
    commit=commit,
    path="README.md",
    line=11
)

print("댓글 작성 완료")