import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)

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
    seo_title: str = "",
    meta_description: str = "",
    focus_keyword: str = "",
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
        "meta": {
            "_yoast_wpseo_title": seo_title,
            "_yoast_wpseo_metadesc": meta_description,
            "_yoast_wpseo_focuskw": focus_keyword,
        },
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


CATEGORY_ID_MAP = {
    "AI 자동화 부업": 2,
    "개발 실전 기록": 3,
    "수익화 전략": 4,
}
