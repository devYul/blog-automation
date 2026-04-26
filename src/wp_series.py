import html
import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

WP_URL = os.getenv("WP_URL", "https://devyul.com")


def fetch_published_posts(per_page: int = 20) -> list[dict]:
    """발행된 WordPress 글을 날짜 오름차순으로 가져옵니다."""
    res = requests.get(
        f"{WP_URL}/wp-json/wp/v2/posts",
        params={
            "status": "publish",
            "per_page": per_page,
            "orderby": "date",
            "order": "asc",
            "_fields": "id,title,link,date",
        },
        timeout=15,
    )
    res.raise_for_status()
    return res.json()


def build_series_context(posts: list[dict]) -> str:
    if not posts:
        return ""

    lines = [f"현재까지 발행된 글 목록 (총 {len(posts)}편):"]
    for i, post in enumerate(posts, 1):
        title = html.unescape(post["title"]["rendered"])
        url = post["link"]
        lines.append(f"{i}편 제목: {title}")
        lines.append(f"{i}편 URL: {url}")

    lines.append(f"\n새로 작성할 글은 {len(posts) + 1}편입니다.")
    return "\n".join(lines)


def get_series_context() -> str:
    """WordPress 발행 글 목록을 시리즈 맥락 문자열로 반환합니다. 실패 시 빈 문자열."""
    try:
        posts = fetch_published_posts()
        return build_series_context(posts)
    except Exception as e:
        print(f"시리즈 맥락 조회 실패 (무시): {e}")
        return ""
