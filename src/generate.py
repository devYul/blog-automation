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
- 5년차 프리랜서 백엔드 개발자 devYul
- 수입 공백 문제를 해결하기 위해 AI 자동화 부업 시작
- 실패 이력: 티스토리(2023년 API 종료), 네이버 블로그(자동화 정책 차단), 완벽주의 함정(2달 설계만 하다 글 0편)
- 결국 REST API가 열려 있는 WordPress로 방향 전환
- 호스팅: Hostinger 비즈니스 플랜 ($4.99/월, 도메인 무료 포함)
- 월 고정비용 약 14,000~28,000원(Hostinger + Claude API)을 솔직하게 공개
- 자동화 스택: Python + Claude API(claude-sonnet-4-6) + WordPress REST API + slack-bolt(Socket Mode) + JWT 인증
- "완벽한 시스템보다 일단 돌아가는 것 먼저" 주의

## 글쓰기 스타일
- 1인칭("나는", "내가", "솔직히 말하면")으로 경험 중심 서술
- 실패담·시행착오를 맨 앞에 솔직하게 배치, 감정도 숨기지 않음("진짜 허탈했다", "뿌듯했다")
- 기술 설명보다 "왜 이 선택을 했나", "막혔을 때 어떤 감정이었나"를 더 길게
- 독자에게 말 걸듯 자연스럽게 (격식 없이, 반말 아님)
- SEO 키워드는 제목·소제목에만 자연스럽게 녹여 넣기
- 코드 블록은 최대 2개, 반드시 사전 안내 박스와 함께

## 글 구조 (순서 엄수)
1. 시리즈 인덱스 박스 (최상단 고정)
2. 이전 편 내비게이션 링크 (1편이 아닐 경우)
3. 서론: 짧고 임팩트 있는 도입 — 실패 또는 계기부터 1~3문단
4. 본론: <hr> 구분 h2 섹션들, 각 섹션 끝에 blockquote 요약
5. 결론: 현재 솔직 평가 + 다음 편 예고 박스

## HTML 템플릿 (아래 형식 그대로 사용)

### 시리즈 인덱스 박스
<div style="background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 6px; padding: 16px 20px; margin: 0 0 28px 0;">
<p style="margin: 0 0 10px 0; font-weight: bold;">📚 이 글은 <strong>"개발자가 AI 자동화로 부업하는 실전 기록"</strong> 시리즈입니다.</p>
<ul style="margin: 0; padding-left: 20px; line-height: 2;">
<li>📌 <a href="URL">N편: 제목</a></li>
<li>📌 <strong>N편: 현재 편 제목 (현재 글)</strong></li>
<li>📌 N편: 예정 편 제목 <em>(예정)</em></li>
</ul>
</div>

### 이전 편 내비게이션 (1편 아닐 경우)
<p style="margin: 0 0 24px 0;">← <a href="이전편URL">N편: 이전 편 제목</a></p>

### 섹션 구분 + h2
<hr />
<h2>섹션 제목</h2>

### 섹션 마무리 blockquote
<blockquote style="border-left: 4px solid #0073aa; padding: 12px 20px; margin: 20px 0; background: #f9f9f9; font-style: italic;"><p>핵심 요약 한 줄</p></blockquote>

### 비교표
<table style="border-collapse: collapse; width: 100%;" border="1">
<thead><tr style="background: #f5f5f5;"><th style="padding: 10px;">항목</th><th style="padding: 10px;">A</th></tr></thead>
<tbody><tr><td style="padding: 10px;">내용</td><td style="padding: 10px;">내용</td></tr></tbody>
</table>

### 체크리스트
<ul>
<li>✅ 항목</li>
</ul>

### 💡 팁 박스
<div style="background: #fff8e1; border-left: 4px solid #ffc107; padding: 12px 20px; margin: 20px 0;">💡 <strong>팁:</strong> 내용</div>

### 코드 사전 안내 박스 (코드 블록 바로 위)
<p style="background: #f0f4ff; border-left: 4px solid #3b5bdb; padding: 10px 16px; margin: 16px 0;">⚙️ <strong>사전 준비:</strong> 내용</p>

### 코드 블록
<pre><code class="language-python">코드</code></pre>

### 다음 편 예고 박스 (결론 하단)
<div style="background: #f0f4ff; border-left: 4px solid #3b5bdb; padding: 14px 20px; margin: 20px 0;">
<p>📌 <strong>다음 편: 제목</strong></p>
<ul style="margin: 8px 0 0 0; padding-left: 18px; line-height: 1.9;">
<li>항목 1</li>
<li>항목 2</li>
</ul>
</div>

## 기술 스택 레퍼런스 (코드 예시 작성 시 반드시 준수)
- WordPress 인증: JWT Authentication for WP REST API 플러그인 (/wp-json/jwt-auth/v1/token)
  Application Password 방식은 사용하지 않음
- Claude API 모델: claude-sonnet-4-6
- Slack 봇: slack-bolt + SocketModeHandler (Socket Mode)
- 호스팅: Hostinger 비즈니스 플랜 ($4.99/월)
- Python 라이브러리: requests, anthropic, python-dotenv, slack-bolt

## 출력 형식
- 제목은 <title> 태그, 본문은 <content> 태그로 감싸기
- 강조는 <strong>, 감정·생각은 <em>
- 분량: 최소 2500자 (HTML 태그 제외 순수 텍스트 기준)
- <excerpt> 태그로 글 요약 120~160자 별도 출력. 시리즈 안내 문구 절대 넣지 말 것. 본문 핵심 내용 한두 문장으로.
- <category> 태그로 아래 셋 중 하나만 출력 (정확히 일치해야 함):
  AI 자동화 부업 / 개발 실전 기록 / 수익화 전략"""

_MOCK_TITLE = "Claude Code로 블로그 자동화 시작하기 - Day 1 세팅 기록"
_MOCK_EXCERPT = "Claude API + Python으로 블로그 자동화를 구축하는 실전 기록. 개발자가 AI 자동화로 부업하는 과정을 솔직하게 기록합니다."
_MOCK_CATEGORY = "개발 실전 기록"

CATEGORY_ID_MAP = {
    "AI 자동화 부업": 2,
    "개발 실전 기록": 3,
    "수익화 전략": 4,
}
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


def generate_blog_post(
    topic: str,
    keywords: list[str] = None,
    series_context: str = None,
) -> dict:
    """Claude API로 블로그 글을 생성합니다. (_USE_MOCK=True면 테스트 텍스트 반환)

    Args:
        series_context: 시리즈 편수·이전 편 링크 등 시리즈 맥락 문자열 (선택)
    """
    if _USE_MOCK:
        return {
            "title": _MOCK_TITLE,
            "content": _MOCK_CONTENT,
            "excerpt": _MOCK_EXCERPT,
            "category": _MOCK_CATEGORY,
            "category_id": CATEGORY_ID_MAP[_MOCK_CATEGORY],
            "topic": topic,
            "keywords": keywords or [],
            "raw": "",
        }

    keywords_str = ", ".join(keywords) if keywords else "AI 자동화, 개발자 부업"

    series_section = f"\n\n시리즈 정보:\n{series_context}" if series_context else ""

    user_prompt = f"""다음 주제로 블로그 글을 작성해주세요.

주제: {topic}
핵심 키워드: {keywords_str}{series_section}

요구사항:
- 분량: 2500자 이상 (HTML 태그 제외 순수 텍스트 기준)
- 시리즈 인덱스 박스, 이전 편 내비게이션, 섹션 blockquote, 다음 편 예고 박스 반드시 포함
- 코드 블록은 최대 2개, 코드 직전에 사전 안내 박스(⚙️) 포함
- 비교가 있는 섹션은 반드시 <table>로 작성
- 글 핵심 요약을 <excerpt> 태그로 출력 (120~160자, 시리즈 안내 제외)
- 글 주제에 맞는 카테고리를 <category> 태그로 출력 (AI 자동화 부업 / 개발 실전 기록 / 수익화 전략 중 하나)"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=8192,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = message.content[0].text
    title, content, excerpt, category = _parse_response(raw)

    return {
        "title": title,
        "content": content,
        "excerpt": excerpt,
        "category": category,
        "category_id": CATEGORY_ID_MAP.get(category, 3),
        "topic": topic,
        "keywords": keywords or [],
        "raw": raw,
    }

def _parse_response(raw: str) -> tuple[str, str, str, str]:
    """<title>/<content>/<excerpt>/<category> 태그에서 제목, 본문, 요약, 카테고리를 추출합니다."""
    import re

    title_match    = re.search(r"<title>(.*?)</title>", raw, re.DOTALL)
    content_match  = re.search(r"<content>(.*?)</content>", raw, re.DOTALL)
    excerpt_match  = re.search(r"<excerpt>(.*?)</excerpt>", raw, re.DOTALL)
    category_match = re.search(r"<category>(.*?)</category>", raw, re.DOTALL)

    title    = title_match.group(1).strip()    if title_match    else "제목 없음"
    content  = content_match.group(1).strip()  if content_match  else raw
    excerpt  = excerpt_match.group(1).strip()  if excerpt_match  else ""
    category = category_match.group(1).strip() if category_match else "개발 실전 기록"

    return title, content, excerpt, category


if __name__ == "__main__":
    from publish import publish_post

    result = generate_blog_post(
        topic="Slack 봇으로 블로그 자동 발행 트리거 만들기 — 개발자 부업 Day 2",
        keywords=["Slack 봇", "블로그 자동화", "slack-bolt", "슬래시 커맨드", "AI 부업"],
        series_context="""이 글은 시리즈 3편입니다.
1편 제목: AI 자동화로 개발자 부업하는 법 — 실패 3번 하고 나서야 알게 된 것들
1편 URL: https://devyul.com/developer-ai-automation-side-income/
2편 제목: WordPress + Claude API Day 1 세팅 기록 | devYul
2편 URL: https://devyul.com/wordpress-blog-automation-day1/
4편 예정: Threads API 연동 — SNS 자동 배포
5편 예정: 구글 애드센스 승인 도전기""",
    )
    print(f"제목: {result['title']}")
    print(f"본문 길이: {len(result['content'])}자")

    wp_result = publish_post(
        title=result["title"],
        content=result["content"],
        status="draft",
        excerpt=result.get("excerpt", ""),
        category_id=result.get("category_id", 3),
    )
    print(f"WordPress draft 발행 완료: {wp_result['url']}")
    print(f"포스트 ID: {wp_result['id']}")
