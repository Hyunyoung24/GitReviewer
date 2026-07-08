# GitReviewer
GitHub PR이 열리면 Claude AI가 자동으로 코드를 리뷰하고 라인 코멘트를 달아주는 봇

## 작동 방식
1. GitHub 저장소에 PR이 열리거나 커밋이 추가되면
2. GitHub webhook이 FastAPI 서버로 이벤트를 전송하고 (`app/main.py`)
3. HMAC-SHA256 서명 검증 후 Redis 큐에 작업 적재
4. RQ 워커가 큐에서 작업을 꺼내 PR의 diff를 추출하고 (`worker.py` > `app/core/reviewer.py`)
5. Claude API로 코드 리뷰를 요청
6. 결과를 GitHub PR 라인 코멘트 + 요약 댓글로 등록하고 DB에 저장 (`app/core/reviewer.py`)
7. 웹 대시보드에서 리뷰 이력 확인 (`app/api/dashboard.py`)

## 기술 스택

| 영역 | 기술 | 이유 |
|------|------|------|
| 백엔드 | FastAPI | 비동기 웹훅 수신에 최적 |
| LLM | Claude API (Sonnet 4.6) | 코드 이해도 최상, 긴 컨텍스트 처리 |
| 비동기 처리 | Redis + RQ | GitHub 웹훅 10초 타임아웃 방지 |
| DB | SQLite | 리뷰 이력 저장 |
| 프론트 | Chart.js | 리뷰 통계 시각화 |

## Claude를 선택한 이유
- 코드 리뷰는 긴 diff 이해와 정확한 버그 탐지가 핵심
- Claude는 코드 이해도가 LLM 중 최상위 수준이며 200K 토큰의 긴 컨텍스트를 처리할 수 있어 대규모 PR도 분석 가능

## 트러블슈팅
### GitHub 웹훅 타임아웃
- Claude API 응답이 수 초에서 수십 초 걸려서 GitHub 웹훅 10초 타임아웃에 걸리는 문제
- Redis 큐를 도입해 웹훅 수신 즉시 200 응답을 보내고, 워커가 백그라운드에서 처리하는 구조로 해결

### 타이밍 공격 방지
- `==` 비교는 앞글자부터 하나씩 비교하다가 다른 글자를 만나면 false를 반환하기에 응답 시간으로 몇 글자까지 맞았는지 추측 가능
- `hmac.compare_digest()` 로 서명 전체를 비교하는 것으로 해결

### 할루시네이션
- Claude가 현재 날짜를 과거로 인식하는 문제
- `import datetime` 후 프롬프트에 오늘 날짜를 명시적으로 포함시켜 해결

### 중복 리뷰 방지
- 같은 PR에 커밋이 추가될 때마다 리뷰가 중복 생성
- 커밋 SHA와 PR 번호로 중복 리뷰 여부를 파악해서 이미 리뷰했을 경우 건너뛰게 처리해서 해결

## 사용법
### 사전 준비
- [ngrok](https://ngrok.com) 설치 및 계정 연동
```bash
ngrok config add-authtoken your_token
```
- WSL에 Redis 설치
```bash
sudo apt-get install redis-server
sudo service redis-server start
```

### GitHub 웹훅 등록
1. 리뷰받을 GitHub 저장소 → Settings → Webhooks → Add webhook
2. Payload URL: `https://ngrok주소/webhook`
3. Content type: `application/json`
4. Secret: `.env`의 `WEBHOOK_SECRET` 값
5. Events: **Pull requests** 선택
6. Add webhook 클릭

### 실행
```bash
# 1. 패키지 설치
pip install -r requirements.txt

# 2. 환경변수 설정 (.env)
ANTHROPIC_API_KEY=클로드 API 키
GITHUB_TOKEN=해당 리포지토리 접근 가능한 토큰
WEBHOOK_SECRET=웹훅 Secret 값
REDIS_URL=redis://localhost:6379

# 3. DB 초기화
python -m app.init_db

# 4. 서버 실행
uvicorn app.main:app --reload --port 8000

# 5. 워커 실행
python worker.py

# 6. ngrok으로 외부 노출
ngrok http 8000

# 7. 대시보드 실행
http://127.0.0.1:8000/dashboard_page
```

> **참고**: Windows 환경에서는 Redis 실행을 위해 WSL(Windows Subsystem for Linux)이 필요합니다.
> ```bash
> wsl --install -d Ubuntu
> sudo apt-get install redis-server
> sudo service redis-server start
> ```

## 추후 계획
- **카테고리 분류**: 버그/스타일/성능/보안으로 리뷰 코멘트를 자동 분류하고 대시보드에 통계 표시
- **Docker화**: docker-compose로 FastAPI + Redis + Worker를 한 번에 구동
- **파일별 분리 리뷰**: 대용량 PR에서 파일 단위로 Claude를 따로 호출해 정확도 향상
- **PostgreSQL 전환**: 배포 환경에서 SQLite → PostgreSQL로 전환
- **(선택) GitHub App 전환**: 현재는 저장소별 수동 웹훅 등록 방식이지만, GitHub App으로 전환하면 누구나 설치해서 쓸 수 있는 서비스로 확장 가능