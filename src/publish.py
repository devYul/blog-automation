import os
import requests
from dotenv import load_dotenv
from generate import generate_blog_post

load_dotenv()

WP_URL = os.getenv("WP_URL", "https://devyul.com")
WP_USERNAME = os.getenv("WP_USERNAME")
WP_PASSWORD = os.getenv("WP_PASSWORD")

JWT_ENDPOINT = f"{WP_URL}/wp-json/jwt-auth/v1/token"

_cached_token: str | None = None


def _get_jwt_token() -> str:
    """JWT 토큰을 발급받습니다. 같은 프로세스 내에서는 재사용합니다."""
    global _cached_token
    if _cached_token:
        return _cached_token

    response = requests.post(
        JWT_ENDPOINT,
        json={"username": WP_USERNAME, "password": WP_PASSWORD},
        timeout=15,
    )
    response.raise_for_status()

    data = response.json()
    if not data.get("token"):
        raise ValueError(f"JWT 토큰 발급 실패: {data}")

    _cached_token = data["token"]
    return _cached_token


def _get_auth_header() -> dict:
    return {"Authorization": f"Bearer {_get_jwt_token()}"}


def publish_post(
    title: str,
    content: str,
    status: str = "publish",
    excerpt: str = "",
    category_id: int = 3,
    categories: list[int] = None,
    tags: list[int] = None,
) -> dict:
    """WordPress REST API로 포스트를 발행합니다."""
    endpoint = f"{WP_URL}/wp-json/wp/v2/posts"
    headers = {**_get_auth_header(), "Content-Type": "application/json"}

    payload = {
        "title": title,
        "content": content,
        "status": status,  # 'publish' | 'draft'
        "excerpt": excerpt,
        "categories": [category_id],
    }
    if categories:
        payload["categories"] = categories
    if tags:
        payload["tags"] = tags

    response = requests.post(endpoint, json=payload, headers=headers, timeout=30)
    response.raise_for_status()

    post = response.json()
    return {
        "id": post["id"],
        "url": post["link"],
        "title": post["title"]["rendered"],
        "status": post["status"],
    }


def generate_and_publish(
    topic: str,
    keywords: list[str] = None,
    status: str = "publish",
    categories: list[int] = None,
    tags: list[int] = None,
) -> dict:
    """글 생성 → WordPress 발행을 한 번에 수행합니다."""
    print(f"[1/2] Claude API로 글 생성 중... (주제: {topic})")
    post_data = generate_blog_post(topic, keywords)
    print(f"     제목: {post_data['title']} ({len(post_data['content'])}자)")

    print("[2/2] WordPress에 발행 중...")
    result = publish_post(
        title=post_data["title"],
        content=post_data["content"],
        status=status,
        categories=categories,
        tags=tags,
    )
    print(f"     발행 완료: {result['url']}")

    return {**result, "topic": topic, "keywords": keywords or []}


if __name__ == "__main__":
    result = generate_and_publish(
        topic="Claude Code로 블로그 자동화 시작하기 - Day 1 세팅 기록",
        keywords=["Claude Code", "블로그 자동화", "AI 부업", "Python", "WordPress"],
        status="draft",
    )
    print(f"\n발행 결과: {result}")
