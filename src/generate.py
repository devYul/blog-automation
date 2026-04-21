import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

# WordPress 발행 로직 테스트용 — 크레딧 충전 후 False로 변경
_USE_MOCK = True

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """당신은 'devYul'이라는 개발자 블로그의 필자입니다.
블로그 주제는 "개발자가 AI 자동화로 부업하는 실전 기록"입니다.

글쓰기 스타일:
- 실전 경험 기반의 솔직하고 구체적인 톤
- 독자가 바로 따라할 수 있는 실용적인 내용
- 코드 예제 포함 (Python 위주)
- SEO를 고려한 자연스러운 키워드 포함
- 한국어로 작성

글 구조:
1. 후킹되는 서론 (왜 이 글을 읽어야 하는가)
2. 본론 (단계별 실전 내용, 소제목 포함)
3. 결론 및 다음 단계 예고

출력 형식: WordPress에 바로 올릴 수 있는 HTML 형식으로 작성해주세요.
제목은 <title> 태그로, 본문은 <content> 태그로 감싸주세요."""

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
        max_tokens=4096,
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
