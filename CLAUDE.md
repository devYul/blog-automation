# devYul 블로그 자동화 프로젝트

## 프로젝트 개요
- 목표: AI 자동화 블로그 운영 + 수익화
- 블로그 주제: 개발자가 AI 자동화로 부업하는 실전 기록
- 운영자: devYul
- 블로그: https://devyul.com (WordPress, Hostinger 호스팅)

## 아키텍처 (2026-07 리팩토링)

**Claude API 직접 호출 제거.** 글은 Claude Code 세션이 직접 작성하고,
Python 스크립트는 발행만 담당한다. → API 토큰 비용 0원.

```
Claude Code가 글 작성 (drafts/epNN.html + epNN.json)
    ↓
python src/publish_draft.py drafts/epNN.json
    ↓
WordPress 발행 → published.json 갱신 → Notion 기록 → Threads 포스팅
```

## 매일 발행 워크플로우 (Claude Code 세션이 수행)

1. **다음 에피소드 확인**: `data/published.json`(발행 이력)과 `data/topics.json`(로드맵)을 읽고,
   아직 발행되지 않은 가장 낮은 episode를 고른다.
2. **글 작성**: `WRITING_GUIDE.md`의 페르소나·스타일·HTML 템플릿을 **반드시** 따라
   본문을 `drafts/epNN.html`로 작성한다. 시리즈 인덱스 박스의 이전 편 링크는
   published.json의 실제 제목·URL을 사용한다.
3. **메타 작성**: `drafts/epNN.json`에 메타데이터 작성 (형식은 아래 참고).
4. **발행**: `python src/publish_draft.py drafts/epNN.json`
   - 테스트만 하려면 `--draft` (WP draft 상태, 이력/Threads 생략)
5. **확인**: 출력된 URL 정상 여부 확인. Notion/Threads 실패는 경고만 출력되며 발행은 유지됨.

### drafts/epNN.json 형식
```json
{
  "episode": 23,
  "title": "글 제목",
  "content_file": "ep23.html",
  "excerpt": "120~160자 요약 (시리즈 안내 금지)",
  "category": "개발 실전 기록",
  "category_id": 3,
  "seo_title": "60자 이내 SEO 제목",
  "meta_description": "120~155자 메타 설명",
  "focus_keyword": "핵심 키워드",
  "threads_text": "Threads 훅 텍스트 (200자 이내, URL/해시태그 금지)"
}
```
카테고리 ID: AI 자동화 부업=2, 개발 실전 기록=3, 수익화 전략=4

## 폴더 구조
- `src/publish_draft.py`: **메인 진입점** — 드래프트 파일 발행 파이프라인
- `src/publish.py`: WordPress REST API 발행 (JWT 인증)
- `src/threads_post.py`: Threads 2단계 포스팅 (본문 + URL 댓글)
- `src/notion_logger.py`: 발행 이력 Notion DB 기록
- `src/wp_series.py`: WP 발행 글 목록 조회 유틸 (검증용)
- `data/topics.json`: 에피소드 로드맵
- `data/published.json`: 발행 이력 (중복 발행 방지의 기준)
- `drafts/`: Claude Code가 작성한 글 원고 보관
- `legacy/`: 구버전 (Claude API 호출 기반 generate.py, slack_bot.py) — 사용 안 함
- `WRITING_GUIDE.md`: 글쓰기 페르소나·스타일·템플릿 가이드

## 주의사항
- 발행 전 반드시 published.json으로 중복 확인 (스크립트가 자동으로 막지만 episode 번호를 잘못 쓰면 소용없음)
- excerpt에 시리즈 안내 문구 넣지 말 것
- threads_text에 URL 넣지 말 것 (Threads 정책 — URL은 댓글로 자동 첨부)
- .env는 절대 커밋 금지
