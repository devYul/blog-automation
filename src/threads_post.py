import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

THREADS_API_BASE = "https://graph.threads.net/v1.0"
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
THREADS_USER_ID = os.getenv("THREADS_USER_ID")


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
    reply_creation_id = _create_container(url, reply_to_id=post_id)
    return _publish_container(reply_creation_id)


def post_to_threads(text: str, url: str) -> dict:
    """Threads에 블로그 포스트를 공유합니다.

    Threads API는 본문 내 URL을 제한하므로 2단계로 나눠 게시합니다.
    Step 1: 훅 텍스트만 본문으로 게시 (URL 없음)
    Step 2: URL을 댓글로 달기 (실패해도 Step 1 성공으로 처리)

    Args:
        text: 게시할 훅 텍스트 (Claude Code가 드래프트에 작성, 200자 이내 권장)
        url: 댓글로 달 블로그 URL

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

    main_text = text.strip()[:490]  # Threads 텍스트 제한(500자) 여유분

    # Step 1: 본문 게시
    main_creation_id = _create_container(main_text)
    thread_id = _publish_container(main_creation_id)
    print(f"[Step 1] 게시 완료: {thread_id}")

    # Step 2: URL 댓글 달기 (실패해도 Step 1 결과 반환)
    reply_id = None
    step2_error = None
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
