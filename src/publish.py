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
    "PLM 마이그레이션": 28,
}

# 블로그 태그 체계 (2026-07 정리: 13종 고정 — 새 태그 남발 금지, 이 중에서 선택)
TAG_ID_MAP = {
    "블로그 자동화": 15,
    "Claude API": 16,
    "AI 부업": 17,
    "WordPress": 18,
    "블로그 수익화": 19,
    "애드센스": 20,
    "SEO": 21,
    "API 연동": 22,
    "트래픽 성장": 23,
    "Python": 24,
    "Next.js": 25,
    "디버깅": 26,
    "레거시 마이그레이션": 27,
}


def resolve_tag_ids(tag_names: list[str]) -> list[int]:
    """태그명 리스트를 WP 태그 ID로 변환합니다. 미등록 태그는 경고 후 건너뜁니다."""
    ids = []
    for name in tag_names or []:
        tag_id = TAG_ID_MAP.get(str(name).strip())
        if tag_id:
            ids.append(tag_id)
        else:
            print(f"      ⚠️ 미등록 태그 무시: {name} (TAG_ID_MAP에 없음)")
    return ids
