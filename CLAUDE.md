# devYul 블로그 자동화 프로젝트

## 프로젝트 개요
- 목표: AI 자동화 블로그 운영 + 수익화
- 블로그 주제: 개발자가 AI 자동화로 부업하는 실전 기록
- 운영자: devYul

## 기술 스택
- Python 3.x
- Claude API (Anthropic)
- WordPress REST API
- Threads API (Meta)
- Slack Bot
- Notion API

## 블로그 정보
- URL: https://devyul.com
- 플랫폼: WordPress 6.9.4
- 호스팅: Hostinger

## 폴더 구조
- src/generate.py: Claude API로 블로그 글 생성
- src/publish.py: WordPress REST API로 자동 발행
- src/threads_post.py: Threads 자동 포스팅
- src/slack_bot.py: 슬랙 명령어 처리
- src/notion_logger.py: 발행 내역 노션 저장

## 기존 연동
- Slack: polyglot-automation-hub/java-core 참고
- Notion: polyglot-automation-hub/java-core 참고
- GitHub: devYul 계정

## 자동화 플로우
슬랙 명령 → Claude API 글 생성 → WordPress 발행 → Threads 포스팅 → Notion 기록