# 오늘의 devYul 블로그 글 작성·발행 지시서

devYul 블로그(https://devyul.com)에 오늘의 글 1편을 작성해서 발행하라.
이 세션은 GitHub Actions 러너에서 실행 중이며, 저장소는 이미 체크아웃되어 있고 의존성(requests, python-dotenv)도 설치되어 있다.

## 절차

1. `CLAUDE.md`의 "매일 발행 워크플로우"와 `WRITING_GUIDE.md`(페르소나 devYul, 글쓰기 스타일, HTML 템플릿)를 읽고 **그대로** 따른다.
2. **중복 방지 가드**: `data/published.json`에 오늘 날짜(Asia/Seoul 기준, `date` 필드)로 이미 발행된 항목이 있으면 아무것도 하지 말고 "오늘 발행 완료됨"만 출력하고 종료한다.
3. `data/topics.json`에서 아직 발행되지 않은 가장 낮은 episode를 고른다. 남은 주제가 없으면 시리즈 흐름에 맞는 새 주제를 정해 다음 번호로 `topics.json`에 추가한 뒤 진행한다.
4. 본문을 `drafts/epNN.html`로 작성한다.
   - 순수 텍스트(태그 제외) 2500자 이상
   - 시리즈 인덱스 박스에는 published.json의 최근 3~4편 실제 제목·URL + 현재 편 + 다음 예정 편
   - WRITING_GUIDE.md의 HTML 템플릿(인덱스 박스, 이전 편 내비게이션, hr+h2 섹션, blockquote 요약, 팁 박스, 다음 편 예고 박스) 준수
5. `drafts/epNN.json` 메타 작성: episode, title, content_file, excerpt(120~160자, 시리즈 안내 금지), category, category_id, seo_title(60자 이내), meta_description(120~155자), focus_keyword, threads_text(200자 이내, URL·해시태그 금지).
6. 발행 실행: `python src/publish_draft.py drafts/epNN.json`
   - WP/Notion/Threads 인증 정보는 환경변수로 주입되어 있다 (WP_URL, WP_USERNAME, WP_PASSWORD, NOTION_TOKEN, NOTION_DASHBOARD_DB_ID, THREADS_ACCESS_TOKEN, THREADS_USER_ID).
   - 환경변수가 비어 있으면 발행하지 말고 어떤 변수가 없는지 명확히 출력한 뒤 실패로 종료한다.
7. 출력된 URL에 GET 요청을 보내 200 응답과 제목을 확인한다.
8. 커밋·푸시는 하지 마라 — 워크플로우의 다음 스텝이 `data/`와 `drafts/` 변경분을 자동 커밋한다.

## 주의

- Claude API(anthropic 패키지)를 호출하지 말 것 — 글은 이 세션이 직접 작성한다.
- Threads 실패는 비치명적(발행은 유지됨). 실패 시 토큰 만료 가능성을 출력에 명시한다.
- 완료 후 발행 글 제목·URL, Notion/Threads 성공 여부를 요약 출력하라.
