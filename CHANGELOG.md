# Changelog

이 프로젝트의 주요 변경사항을 기록합니다.
형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 따르며,
[Semantic Versioning](https://semver.org/lang/ko/)을 준수합니다.

## [Unreleased]

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