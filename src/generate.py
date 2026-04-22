import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

# WordPress 발행 로직 테스트용 — 크레딧 충전 후 False로 변경
_USE_MOCK = False

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """당신은 'devYul'이라는 개발자 블로그의 필자입니다.
블로그 주제는 "개발자가 AI 자동화로 부업하는 실전 기록"입니다.

## 페르소나
- 직장 다니면서 AI 자동화로 부업을 시도하는 평범한 백엔드 개발자
- 처음엔 티스토리, 네이버 블로그로 자동화를 시도했지만 번번이 막혔음
  - 티스토리: 2023년 오픈 API 사실상 종료, 외부 앱 연동 불가
  - 네이버 블로그: 자동화 자체를 정책으로 차단, 봇 감지 즉시 제재
  - 결국 REST API가 열려있는 WordPress로 방향 전환
- 완벽한 시스템을 만들려다 아무것도 못 한 경험 있음 → 지금은 일단 돌아가게 먼저 만드는 주의
- 비용 걱정도 솔직하게 언급 (Claude API 크레딧, 호스팅비 등)

## 글쓰기 스타일
- 1인칭 ("나는", "내가", "솔직히", "사실")으로 개인 경험 중심 서술
- 실패담·시행착오를 숨기지 않고 오히려 앞에 배치
- 코드 블록은 꼭 필요한 경우에만, 최대 1~2개로 최소화
- 기술 설명보다 "왜 이 선택을 했나", "막혔을 때 어떤 감정이었나"를 더 길게 서술
- 독자에게 말 걸듯 자연스러운 문체 (격식 없이, 그렇다고 반말도 아님)
- SEO 키워드는 제목·소제목에만 자연스럽게 녹여 넣기

## 글 구조
1. 서론: 왜 이걸 시작했는지 — 실패 경험이나 계기부터 솔직하게
2. 본론: 시행착오 → 현재 방향 → 실제 겪은 일 순서로 스토리텔링
3. 결론: 현재 상태 솔직 평가 + 다음 편 예고 (구체적으로)

## 시각적 요소 (반드시 포함)

### 1. 비교표 — 플랫폼·도구를 비교하는 섹션이 있으면 반드시 HTML <table>로 작성
<table> 예시 구조:
<table style="border-collapse:collapse;width:100%;" border="1">
  <thead><tr style="background:#f5f5f5;"><th>항목</th><th>A</th><th>B</th></tr></thead>
  <tbody><tr><td>...</td><td>...</td><td>...</td></tr></tbody>
</table>

### 2. 섹션 요약 blockquote — 각 h2 섹션 마무리에 핵심 한 줄 요약
<blockquote style="border-left:4px solid #0073aa;padding:12px 20px;margin:20px 0;background:#f9f9f9;font-style:italic;">
  핵심 요약 한 줄
</blockquote>

### 3. 체크리스트 — 단계·할 일 목록은 ✅ 이모지 + <ul> 태그
<ul>
  <li>✅ 항목 1</li>
  <li>✅ 항목 2</li>
</ul>

### 4. 실용 팁 콜아웃 — 독자에게 실질적으로 도움 되는 팁은 아래 박스로 강조
<div style="background:#fff8e1;border-left:4px solid #ffc107;padding:12px 20px;margin:20px 0;">
  💡 <strong>팁:</strong> 팁 내용
</div>

### 5. 섹션 구분 — 모든 h2 섹션 사이에 <hr> 태그 삽입

## 출력 형식
WordPress에 바로 올릴 수 있는 HTML로 작성해주세요.
- 제목은 <title> 태그, 본문은 <content> 태그로 감싸기
- 소제목은 <h2>, <h3> 사용
- 강조는 <strong>, 개인 생각·감정은 <em> 활용
- 분량: 최소 2500자 이상 (HTML 태그 제외 순수 텍스트 기준)"""

_MOCK_TITLE = "Claude Code로 블로그 자동화 시작하기 - Day 1 세팅 기록"
_MOCK_CONTENT = """<h2>왜 블로그 자동화를 시작했나</h2>
<p>개발자로 일하면서 <strong>AI 자동화</strong>로 부업을 만들 수 있다면 어떨까? 그 첫 번째 실험이 바로 이 블로그다.
매일 직접 글을 쓰는 대신 <strong>Claude Code</strong>와 <strong>Python</strong>으로 자동화 파이프라인을 구축해서
<strong>WordPress</strong>에 자동 발행하는 시스템을 만들기로 했다.</p>

<h2>Day 1 목표</h2>
<p>오늘의 목표는 단순하다. 환경 세팅을 완료하고 글 하나를 자동으로 발행해보는 것.</p>
<ul>
  <li>Python 환경 구성 + 패키지 설치</li>
  <li>Claude API 연동 (<code>generate.py</code>)</li>
  <li>WordPress REST API + JWT 인증 연동 (<code>publish.py</code>)</li>
</ul>

<h2>실제 세팅 과정</h2>
<h3>1. 패키지 설치</h3>
<pre><code class="language-python">pip install anthropic python-dotenv requests</code></pre>

<h3>2. .env 구성</h3>
<pre><code class="language-python">ANTHROPIC_API_KEY=sk-ant-...
WP_URL=https://devyul.com
WP_USERNAME=devyul0206@gmail.com
WP_PASSWORD=your_password</code></pre>

<h3>3. JWT 토큰으로 WordPress 인증</h3>
<p>Application Password가 비활성화되어 있어서 <strong>JWT Authentication for WP REST API</strong> 플러그인으로 대체했다.
토큰을 한 번 발급받아 캐싱하면 같은 프로세스 안에서 재사용할 수 있어 효율적이다.</p>
<pre><code class="language-python">response = requests.post(
    "https://devyul.com/wp-json/jwt-auth/v1/token",
    json={"username": WP_USERNAME, "password": WP_PASSWORD},
)
token = response.json()["token"]</code></pre>

<h2>오늘의 결과</h2>
<p>글 생성 → WordPress draft 발행까지 파이프라인 연결 완료. 다음 단계는 Slack 명령어로 트리거하는 것이다.</p>"""


def generate_blog_post(topic: str, keywords: list[str] = None) -> dict:
    """Claude API로 블로그 글을 생성합니다. (_USE_MOCK=True면 테스트 텍스트 반환)"""
    if _USE_MOCK:
        return {
            "title": _MOCK_TITLE,
            "content": _MOCK_CONTENT,
            "topic": topic,
            "keywords": keywords or [],
            "raw": "",
        }

    keywords_str = ", ".join(keywords) if keywords else "AI 자동화, 개발자 부업"

    user_prompt = f"""다음 주제로 블로그 글을 작성해주세요.

주제: {topic}
핵심 키워드: {keywords_str}

요구사항:
- 분량: 1500자 이상 (HTML 포함)
- 코드 블록이 있으면 <pre><code class="language-python"> 태그 사용
- 소제목은 <h2>, <h3> 태그 사용
- 중요 키워드는 <strong> 태그로 강조"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = message.content[0].text
    title, content = _parse_response(raw)

    return {
        "title": title,
        "content": content,
        "topic": topic,
        "keywords": keywords or [],
        "raw": raw,
    }

def _parse_response(raw: str) -> tuple[str, str]:
    """<title>/<content> 태그에서 제목과 본문을 추출합니다."""
    import re

    title_match = re.search(r"<title>(.*?)</title>", raw, re.DOTALL)
    content_match = re.search(r"<content>(.*?)</content>", raw, re.DOTALL)

    title = title_match.group(1).strip() if title_match else "제목 없음"
    content = content_match.group(1).strip() if content_match else raw

    return title, content


if __name__ == "__main__":
    result = generate_blog_post(
        topic="Claude API로 블로그 자동화 구축하기",
        keywords=["Claude API", "블로그 자동화", "AI 부업", "Python"],
    )
    print(f"제목: {result['title']}")
    print(f"본문 길이: {len(result['content'])}자")
    print("--- 본문 미리보기 ---")
    print(result["content"][:500])
