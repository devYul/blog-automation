import json
import os
from pathlib import Path

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from generate import generate_blog_post
from notion_logger import log_to_dashboard
from publish import publish_post
from threads_post import post_to_threads
from wp_series import get_series_context

load_dotenv(override=True)

app = App(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET"),
)

_TOPICS_PATH = Path(__file__).parent.parent / "data" / "topics.json"
_PUBLISHED_PATH = Path(__file__).parent.parent / "data" / "published.json"


def _load_published() -> list[dict]:
    with open(_PUBLISHED_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save_published(published: list) -> None:
    with open(_PUBLISHED_PATH, "w", encoding="utf-8") as f:
        json.dump(published, f, ensure_ascii=False, indent=2)


def _load_topics() -> list[dict]:
    with open(_TOPICS_PATH, encoding="utf-8") as f:
        return json.load(f)


def build_series_context(episode: int) -> str:
    """현재 편수 기준으로 series_context 자동 생성"""
    topics = _load_topics()

    context = f"이 글은 시리즈 {episode}편입니다.\n"
    for p in _load_published():
        context += f"{p['ep']}편 제목: {p['title']}\n{p['ep']}편 URL: {p['url']}\n"
    for t in topics:
        if t["episode"] > episode:
            context += f"{t['episode']}편 예정: {t['topic']}\n"

    return context


def _next_topic() -> dict | None:
    """topics.json에서 다음 미발행 주제를 반환합니다. 없으면 None."""
    published_eps = {p["ep"] for p in _load_published()}
    topics = _load_topics()
    for t in sorted(topics, key=lambda x: x["episode"]):
        if t["episode"] not in published_eps:
            return t
    return None


@app.command("/blog")
def handle_blog(ack, respond, command):
    ack()  # Slack 3초 제한 내 즉시 응답

    text = command.get("text", "").strip()

    # new: 새 시리즈 시작
    if text.lower().startswith("new:"):
        topic = text[4:].strip()
        if not topic:
            respond("주제를 입력해주세요.\n예) `/blog new: 새 시리즈 첫 글 주제`")
            return
        keywords = None
        episode = None
        series_context = None
        mode_label = "새 시리즈 시작"

    # 직접 입력한 주제
    elif text:
        topic = text
        keywords = None
        episode = len(_load_published()) + 1
        series_context = build_series_context(episode)
        mode_label = f"시리즈 {episode}편 (직접 입력)"

    # 자동: topics.json 다음 주제
    else:
        next_t = _next_topic()
        if not next_t:
            respond("📋 topics.json에 남은 예정 주제가 없습니다.\n직접 주제를 입력해주세요: `/blog 주제`")
            return
        topic = next_t["topic"]
        keywords = next_t.get("keywords")
        episode = next_t["episode"]
        series_context = build_series_context(episode)
        mode_label = f"시리즈 {episode}편 (자동)"
        respond(f"📋 topics.json에서 {episode}편 자동 로드: {topic}")

    respond(f"⏳ *`{topic}`* 글 생성 중... ({mode_label}) 잠시만 기다려주세요.")

    try:
        post_data = generate_blog_post(topic, keywords=keywords, series_context=series_context)
        result = publish_post(
            title=post_data["title"],
            content=post_data["content"],
            status="publish",
            excerpt=post_data.get("excerpt", ""),
            category_id=post_data.get("category_id", 3),
            seo_title=post_data.get("seo_title", ""),
            meta_description=post_data.get("meta_description", ""),
            focus_keyword=post_data.get("focus_keyword", ""),
        )

        # published.json 자동 업데이트
        if episode is not None:
            try:
                published = _load_published()
                published.append({"ep": episode, "title": result["title"], "url": result["url"]})
                _save_published(published)
            except Exception as e:
                print(f"published.json 저장 실패: {e}")

        # Notion 대시보드 기록
        try:
            log_to_dashboard(
                title=result["title"],
                category=post_data.get("category", "개발 실전 기록"),
                url=result["url"],
                threads=True,
            )
        except Exception as e:
            print(f"Notion 기록 실패 (발행은 성공): {e}")

        # Threads 자동 포스팅
        threads_result = None
        threads_error = None
        try:
            threads_result = post_to_threads(
                title=result["title"],
                content=post_data["content"],
                url=result["url"],
            )
        except Exception as te:
            threads_error = str(te)

        fields = [
            {"type": "mrkdwn", "text": f"*모드*\n{mode_label}"},
            {"type": "mrkdwn", "text": f"*제목*\n{result['title']}"},
            {"type": "mrkdwn", "text": f"*URL*\n{result['url']}"},
        ]
        if threads_result:
            fields.append({"type": "mrkdwn", "text": f"*Threads*\n{threads_result['url']}"})
        elif threads_error:
            fields.append({"type": "mrkdwn", "text": f"*Threads*\n⚠️ 실패: {threads_error}"})

        respond(
            blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": "✅ *블로그 글 발행 완료!*"},
                },
                {"type": "section", "fields": fields},
                {"type": "divider"},
            ]
        )
    except Exception as e:
        respond(f"❌ *글 생성 실패*\n주제: {topic}\n오류: {e}")


if __name__ == "__main__":
    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    print("⚡ Slack bot 시작 (Socket Mode)")
    handler.start()
