import html
import os
import re
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

THREADS_API_BASE = "https://graph.threads.net/v1.0"
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
THREADS_USER_ID = os.getenv("THREADS_USER_ID")

HASHTAGS = "#개발기록 #Python #자동화 #블로그개발 #사이드프로젝트"

_SANITIZE_RULES = [
    # 부업 + 조사/활용형 먼저 처리
    (r"부업하[는기고]", "사이드 프로젝트"),
    (r"부업으로", "사이드 프로젝트로"),
    (r"부업을", "사이드 프로젝트를"),
    (r"부업이", "사이드 프로젝트가"),
    (r"부업은", "사이드 프로젝트는"),
    (r"부업[^\s]*", "사이드 프로젝트"),
    # 수익 관련 단어 제거
    (r"수익\S*", ""),
    # 자동화로 돈/수입 류 표현
    (r"자동화로\s+(돈|수입|소득|매출)\s+\S+", "자동화 구축"),
    # 금액 표현
    (r"(월|일|연)\s*\d+[만천백]?\s*원", ""),
]


def _sanitize(text: str) -> str:
    for pattern, repl in _SANITIZE_RULES:
        text = re.sub(pattern, repl, text)
    return re.sub(r"\s{2,}", " ", text).strip()


def _strip_tags(raw: str) -> str:
    text = re.sub(r"<[^>]+>", "", raw)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _extract_summary(content: str) -> str:
    # 1. <h2>, <h3> 블록 제거
    content = re.sub(r"<h[23][^>]*>.*?</h[23]>", "", content, flags=re.DOTALL)

    # 2. 첫 번째 유효한 <p> 추출 (📌/📚 시리즈 인덱스 단락 건너뜀)
    paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", content, re.DOTALL)
    summary = ""
    for p in paragraphs:
        text = _strip_tags(p)
        if not text or text.startswith(("📌", "📚")):
            continue
        # 3. 단락 내 📌 이후 내용 제거
        if "📌" in text:
            text = text[: text.index("📌")].rstrip()
        if text:
            summary = text
            break

    # 4~5. 150자 자르기 + "..." 마무리
    if len(summary) > 150:
        cut = summary[:150].rstrip()
        # 단어 중간 자르기 방지: 마지막 공백 기준으로 자름
        last_space = cut.rfind(" ")
        summary = (cut[:last_space] if last_space > 100 else cut) + "..."

    return summary


def _build_post_text(title: str, content: str) -> str:
    summary = _sanitize(_extract_summary(content))
    clean_title = _sanitize(title)
    return f"📝 {clean_title}\n\n{summary}\n\n{HASHTAGS}"


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
    res.raise_for_status()
    return res.json()["id"]


def post_to_threads(title: str, content: str, url: str) -> dict:
    """Threads에 블로그 포스트를 공유합니다.
    메인 글(제목+요약+해시태그) 발행 후 첫 번째 댓글로 링크를 답니다.

    Returns:
        {"id": str, "url": str, "reply_id": str, "text": str}
    Raises:
        requests.HTTPError: API 호출 실패 시
        ValueError: 환경변수 누락 시
    """
    if not THREADS_ACCESS_TOKEN or THREADS_ACCESS_TOKEN == "your_threads_access_token":
        raise ValueError("THREADS_ACCESS_TOKEN이 설정되지 않았습니다.")
    if not THREADS_USER_ID or THREADS_USER_ID == "your_threads_user_id":
        raise ValueError("THREADS_USER_ID가 설정되지 않았습니다.")

    main_text = _build_post_text(title, content)

    # Step 1~2: 메인 글 게시
    main_creation_id = _create_container(main_text)
    thread_id = _publish_container(main_creation_id)

    # Step 3~4: 링크 댓글 게시
    reply_text = f"📝 전체 글 보기 → {url}"
    reply_creation_id = _create_container(reply_text, reply_to_id=thread_id)
    reply_id = _publish_container(reply_creation_id)

    return {
        "id": thread_id,
        "url": f"https://www.threads.net/@devyul/post/{thread_id}",
        "reply_id": reply_id,
        "text": main_text,
    }


if __name__ == "__main__":
    result = post_to_threads(
        title="Claude Code로 블로그 자동화 시작하기 - Day 1",
        content="<p>AI 자동화로 부업을 만들기 위해 WordPress + Claude API 파이프라인을 구축했습니다.</p>",
        url="https://devyul.com/sample-post",
    )
    print(f"Threads 포스팅 완료: {result['url']}")
    print(f"내용:\n{result['text']}")
