# Changelog

이 프로젝트의 주요 변경사항을 기록합니다.
형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 따르며,
[Semantic Versioning](https://semver.org/lang/ko/)을 준수합니다.

## [0.8.2] - 2026-09-09
### Added
- 대시보드 다크/라이트 모드 전환 버튼 (달/해 아이콘, localStorage 저장)
- 대시보드 차트 색상 모드별 전환 (바 차트, 도넛 차트, 축/범례 텍스트)
- FontAwesome 아이콘 적용 (통계 카드, 섹션 제목, GitHub 링크)

### Fixed
- 대시보드 JS: 중복 `/config` fetch 호출 제거 (race condition으로 커스텀 프롬프트 미복원 문제)
- 대시보드 JS: 중복 `promptStyle` change 이벤트 리스너 정리
- 대시보드 JS: `.catch()` 범위 축소 — JS 런타임 에러 시 "서버가 실행 중이 아닙니다" 오표시 방지
- 테이블 인라인 스타일을 CSS 클래스(`.td-muted`, `.td-sub`)로 교체하여 다크모드 대응

### Changed
- 대시보드 섹션 간 간격 통일 (`margin-bottom: 1rem`)

## [0.8.1] - 2026-09-09
### Added
- GUI 대시보드 열기 버튼 추가
- 서버 미실행 시 대시보드에 안내 메시지 표시

### Fixed
- CSS/JS 경로를 Railway 절대경로에서 상대경로(`/static/...`)로 변경
- GUI 중복 윈도우 생성 방지
- subprocess 호출 시 `CREATE_NO_WINDOW` 플래그 추가
- exe 빌드 시 불필요한 frozen 체크 제거

## [0.8.0] - 2026-09-03
### Added
- 로컬 실행용 GUI 구현

### Security
- `WEBHOOK_SECRET` 미설정 시 서명 검증을 건너뛰던 동작을 요청 거부(401)로 변경
- `/config` 엔드포인트에 `CONFIG_TOKEN` 기반 Bearer 토큰 인증 추가
- 서버 시작 시 `WEBHOOK_SECRET`, `CONFIG_TOKEN` 미설정 경고 로그 출력

## [0.7.0] - 2026-09-02
### Added
- 리뷰 설정 패널 (아코디언 UI)
- 리뷰 스타일 선택 (일반/보안/성능/초보자/커스텀)
- 커스텀 프롬프트 직접 입력 기능
- 현재 프롬프트 미리보기 패널
- 토큰 수 선택 (3000/5000/8000)
- 설정 저장 토스트 알림
- 페이지 로드 시 설정값 자동 복원
- 서버사이드 저장소 필터링

### Security
- Docker 이미지에 `.env`, DB 백업, `node_modules` 등 로컬 전용 파일이 딸려 들어가지 않도록 `.dockerignore`를 화이트리스트 방식으로 추가

### Fixed
- requirements.txt 인코딩이 UTF-16으로 되돌아가 있던 것을 UTF-8로 재변환
- 커스텀 프롬프트가 워커에 전달되지 않던 버그 수정

## [0.6.1] - 2026-07-28
### Fixed
- diff 내 백슬래시로 인한 Claude 응답 JSON 파싱 실패(`Invalid \escape`) 문제 해결
- 프롬프트 기반 JSON 파싱 → Claude API tool use(함수 호출) 구조화 출력으로 전환
- 통계 카드의 저장소 수가 현재 페이지 리뷰 기준으로 집계되어 실제보다 적게 표시되던 문제 해결 (`repo_counts` 기준으로 변경)

## [0.6.0] - 2026-07-27
### Added
- 대시보드 헤더 (다크 테마, GitHub/문서 링크)
- 통계 카드 (총 리뷰 수, 버그, 보안 이슈, 저장소 수)
- 저장소 드롭다운 필터 + PR 제목 검색
- 페이지네이션
- PostgreSQL 전환 지원 (`DATABASE_URL` 환경변수로 SQLite/PostgreSQL 분기)

### Changed
- 대시보드 UI 전면 개편 (헤더, 통계 카드, 테이블 스타일 개선)
- Render 배포 시도 후 Railway로 복귀 (안정성 우선)

### Fixed
- iframe 환경에서 CSS/JS 절대경로로 변경 (키오스크 대응)
- 캐시 문제로 인한 스타일 미적용 해결 (`?v=2` 쿼리 추가)

## [0.5.0] - 2026-07-10
### Added
- 카테고리(bug/style/performance/security)·심각도(info/caution/warning) 분류
- 카테고리별 코멘트 도넛 차트 대시보드 추가
- Docker + docker-compose 컨테이너화 (FastAPI + Redis + Worker)

### Changed
- 대시보드 UI 개선 (차트 레이아웃, PR 배지, 상태 배지 한국어화)
- README Docker 실행 가이드 및 .env 설명 보완

## [0.4.0] - 2026-07-08
### Added
- 라인 코멘트 DB 저장 (ReviewComment 테이블)

### Fixed
- 커밋 SHA + PR 번호 기준 중복 리뷰 방지

### Changed
- requirements.txt 인코딩 UTF-16 → UTF-8
- .gitignore 정리

### Docs
- README 작성 (프로젝트 개요, 아키텍처, 웹훅 가이드, Windows 가이드, .env 설명)

### Style
- 대시보드 UI 부분적 개선
- 대시보드 시간 표시 KST 적용

## [0.3.0] - 2026-07-07
### Added
- Chart.js 대시보드 (리뷰 이력 테이블)
- 리뷰 상세 모달 (마크다운 렌더링)

## [0.2.0] - 2026-07-07
### Added
- GitHub Webhook과 Claude 리뷰 로직 연결
- SQLite 리뷰 이력 저장 (SQLAlchemy ORM)
- Redis + RQ 기반 비동기 워커 처리

### Fixed
- Claude 날짜 할루시네이션 (프롬프트에 현재 날짜 명시)

## [0.1.0] - 2026-07-07
### Added
- 프로젝트 초기 세팅 (.gitignore, requirements.txt)
- Claude API + GitHub PR 코멘트 연동 검증