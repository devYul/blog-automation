import html
import os
import re
import requests
import anthropic
from dotenv import load_dotenv

load_dotenv(override=True)

THREADS_API_BASE = "https://graph.threads.net/v1.0"
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
THREADS_USER_ID = os.getenv("THREADS_USER_ID")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


def _strip_tags(raw: str) -> str:
    text = re.sub(r"<[^>]+>", "", raw)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _generate_threads_text(title: str, content: str) -> str:
    """Claude API로 Threads 본문 텍스트를 생성합니다."""
    plain_content = _strip_tags(content)[:500]

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": (
                    f"다음 블로그 글을 Threads에 올릴 짧은 텍스트로 만들어줘.\n\n"
                    f"제목: {title}\n내용: {plain_content}\n\n"
                    "조건:\n"
                    "- 200자 이내\n"
                    "- 해시태그 없음\n"
                    "- URL 없음\n"
                    "- 숫자+반전 구조 (예: '자동화 2주 했더니\\n\\n방문자: 극소수\\n수익: 0원\\n후회: 없음')\n"
                    "- 개행으로 구분\n"
                    "- 짧고 임팩트 있게\n"
                    "텍스트만 출력해줘."
                ),
            }
        ],
    )
    return message.content[0].text.strip()[:200]


def _create_container(text: str, reply_to_id: str = None) -> str:
    """Threads 미디어 컨테이너를 생성하고 creation_id를 반환합니다."""
    params = {
        "media_type": "TEXT",
        "text": text,
        "access_token": THREADS_ACCESS_TOKEN,
    }
    if reply_to_id:
        params["reply_to_id"] = reply_to_id

    res = requests.post(
        f"{THREADS_API_BASE}/{THREADS_USER_ID}/threads",
        params=params,
        timeout=15,
    )
    if not res.ok:
        print(f"[ERROR] 컨테이너 생성 실패: {res.status_code}\n{res.text}")
        res.raise_for_status()
    return res.json()["id"]


def _publish_container(creation_id: str) -> str:
    """컨테이너를 게시하고 thread_id를 반환합니다."""
    res = requests.post(
        f"{THREADS_API_BASE}/{THREADS_USER_ID}/threads_publish",
        params={
            "creation_id": creation_id,
            "access_token": THREADS_ACCESS_TOKEN,
        },
        timeout=15,
    )
    if not res.ok:
        print(f"[ERROR] 게시 실패: {res.status_code}\n{res.text}")
        res.raise_for_status()
    return res.json()["id"]


def _post_url_reply(post_id: str, url: str) -> str:
    """게시물에 URL을 댓글로 달고 reply_id를 반환합니다."""
    # Threads reply: /{user_id}/threads with reply_to_id → threads_publish
    reply_creation_id = _create_container(url, reply_to_id=post_id)
    return _publish_container(reply_creation_id)


def post_to_threads(title: str, content: str, url: str) -> dict:
    """Threads에 블로그 포스트를 공유합니다.

    Step 1: Claude로 생성한 텍스트를 본문으로 게시 (URL 없음)
    Step 2: URL을 댓글로 달기 (실패해도 Step 1 성공으로 처리)

    Returns:
        {"id": str, "url": str, "reply_id": str | None, "text": str, "step2_error": str | None}
    Raises:
        ValueError: 환경변수 누락 시
        requests.HTTPError: Step 1 실패 시
    """
    if not THREADS_ACCESS_TOKEN or THREADS_ACCESS_TOKEN == "your_threads_access_token":
        raise ValueError("THREADS_ACCESS_TOKEN이 설정되지 않았습니다.")
    if not THREADS_USER_ID or THREADS_USER_ID == "your_threads_user_id":
        raise ValueError("THREADS_USER_ID가 설정되지 않았습니다.")

    # Step 1: Claude로 텍스트 생성 후 본문 게시
    print("[Step 1] Claude로 텍스트 생성 중...")
    main_text = _generate_threads_text(title, content)
    print(f"[Step 1] 생성된 텍스트:\n{main_text}\n")

    main_creation_id = _create_container(main_text)
    thread_id = _publish_container(main_creation_id)
    print(f"[Step 1] 게시 완료: {thread_id}")

    # Step 2: URL 댓글 달기 (실패해도 Step 1 결과 반환)
    reply_id = None
    step2_error = None
    print("[Step 2] URL 댓글 달기...")
    try:
        reply_id = _post_url_reply(thread_id, url)
        print(f"[Step 2] 댓글 완료: {reply_id}")
    except Exception as e:
        step2_error = str(e)
        print(f"[Step 2] 댓글 실패 (본문 게시는 성공): {step2_error}")

    return {
        "id": thread_id,
        "url": f"https://www.threads.net/@devyul/post/{thread_id}",
        "reply_id": reply_id,
        "text": main_text,
        "step2_error": step2_error,
    }


if __name__ == "__main__":
    result = post_to_threads(
        title="Claude Code로 블로그 자동화 시작하기 - Day 1",
        content=(
            "<p>AI 자동화로 사이드 프로젝트를 만들기 위해 "
            "WordPress + Claude API 파이프라인을 구축했습니다. "
            "처음 2주 동안 방문자는 극소수였지만 시스템은 안정적으로 돌아가고 있습니다.</p>"
        ),
        url="https://devyul.com/sample-post",
    )
    print(f"\n포스팅 완료: {result['url']}")
    if result["reply_id"]:
        print(f"URL 댓글 ID: {result['reply_id']}")
    if result["step2_error"]:
        print(f"Step 2 실패: {result['step2_error']}")
    print(f"\n본문:\n{result['text']}")
