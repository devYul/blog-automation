import os

from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from generate import generate_blog_post
from publish import publish_post
from threads_post import post_to_threads

load_dotenv()

app = App(
    token=os.getenv("SLACK_BOT_TOKEN"),
    signing_secret=os.getenv("SLACK_SIGNING_SECRET"),
)


@app.command("/blog")
def handle_blog(ack, respond, command):
    ack()  # Slack 3초 제한 내 즉시 응답

    topic = command.get("text", "").strip()
    if not topic:
        respond("사용법: `/blog 주제`\n예) `/blog AI 자동화로 부업하는 법`")
        return

    respond(f"⏳ *`{topic}`* 글 생성 중... 잠시만 기다려주세요.")

    try:
        post_data = generate_blog_post(topic)
        result = publish_post(
            title=post_data["title"],
            content=post_data["content"],
            status="publish",
            excerpt=post_data.get("excerpt", ""),
        )

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
            {"type": "mrkdwn", "text": f"*상태*\n발행 완료 (publish)"},
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
