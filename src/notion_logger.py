import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DASHBOARD_DB_ID = os.getenv("NOTION_DASHBOARD_DB_ID")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def log_to_dashboard(
    title: str,
    category: str,
    url: str,
    threads: bool = False,
    date: str = None,
) -> dict:
    """발행된 글을 Notion 대시보드 DB에 기록"""
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    data = {
        "parent": {"database_id": DASHBOARD_DB_ID},
        "properties": {
            "제목": {"title": [{"text": {"content": title}}]},
            "카테고리": {"select": {"name": category}},
            "발행일": {"date": {"start": date}},
            "URL": {"url": url},
            "Treads": {"checkbox": threads},
            "SEO점수": {"select": {"name": "확인필요"}},
            "메모": {"rich_text": [{"text": {"content": ""}}]},
        },
    }

    res = requests.post(
        "https://api.notion.com/v1/pages",
        headers=HEADERS,
        json=data,
    )
    res.raise_for_status()
    return res.json()


if __name__ == "__main__":
    result = log_to_dashboard(
        title="테스트 글",
        category="개발 실전 기록",
        url="https://devyul.com/test",
        threads=False,
    )
    print("Notion 기록 완료:", result.get("id"))
