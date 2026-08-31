# Changelog

이 프로젝트의 주요 변경사항을 기록합니다.
형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 따르며,
[Semantic Versioning](https://semver.org/lang/ko/)을 준수합니다.

## [Unreleased]
### Security
- Docker 이미지에 `.env`, DB 백업, `node_modules` 등 로컬 전용 파일이 딸려 들어가지 않도록 `.dockerignore`를 화이트리스트 방식(`app/`, `worker.py`, `requirements.txt`만 허용)으로 추가

### Fixed
- requirements.txt 인코딩이 UTF-16으로 되돌아가 있던 것을 UTF-8로 재변환

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