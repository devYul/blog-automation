import os

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


@app.command("/blog")
def handle_blog(ack, respond, command):
    ack()  # Slack 3초 제한 내 즉시 응답

    text = command.get("text", "").strip()
    if not text:
        respond(
            "사용법:\n"
            "• `/blog 주제` — 기존 시리즈 이어서 작성\n"
            "• `/blog new: 주제` — 새 시리즈 1편으로 시작\n\n"
            "예) `/blog AI 자동화 수익 첫 달 결산`\n"
            "예) `/blog new: 구글 애드센스 승인 도전기`"
        )
        return

    # new: 접두어 파싱
    new_series = text.lower().startswith("new:")
    topic = text[4:].strip() if new_series else text

    if not topic:
        respond("주제를 입력해주세요.\n예) `/blog new: 새 시리즈 첫 글 주제`")
        return

    mode_label = "새 시리즈 시작" if new_series else "시리즈 이어서"
    respond(f"⏳ *`{topic}`* 글 생성 중... ({mode_label}) 잠시만 기다려주세요.")

    try:
        series_context = None if new_series else get_series_context()

        post_data = generate_blog_post(topic, series_context=series_context)
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
            {"type": "mrkdwn", "text": f"*주제*\n{topic}"},
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
