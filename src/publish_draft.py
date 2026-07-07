"""드래프트 파일 기반 발행 파이프라인.

Claude Code가 작성한 초안(drafts/epNN.json + epNN.html)을 받아
WordPress 발행 → published.json 갱신 → Notion 기록 → Threads 포스팅을 수행합니다.

사용법:
    python src/publish_draft.py drafts/ep23.json              # 실제 발행
    python src/publish_draft.py drafts/ep23.json --draft      # WP draft로만 올림
    python src/publish_draft.py drafts/ep23.json --skip-threads
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from notion_logger import log_to_dashboard
from publish import publish_post
from threads_post import post_to_threads

ROOT = Path(__file__).parent.parent
PUBLISHED_PATH = ROOT / "data" / "published.json"

REQUIRED_FIELDS = ["episode", "title", "excerpt", "category", "category_id",
                   "seo_title", "meta_description", "focus_keyword", "threads_text"]


def load_draft(draft_path: Path) -> dict:
    """드래프트 메타(JSON)와 본문(HTML)을 로드하고 필수 필드를 검증합니다."""
    with open(draft_path, encoding="utf-8") as f:
        draft = json.load(f)

    missing = [k for k in REQUIRED_FIELDS if not draft.get(k)]
    if missing:
        raise ValueError(f"드래프트 필수 필드 누락: {missing}")

    content_file = draft.get("content_file", draft_path.stem + ".html")
    content_path = draft_path.parent / content_file
    if not content_path.exists():
        raise FileNotFoundError(f"본문 파일 없음: {content_path}")

    draft["content"] = content_path.read_text(encoding="utf-8")
    plain_len = len("".join(draft["content"].split()))
    if plain_len < 500:
        raise ValueError(f"본문이 너무 짧습니다 ({plain_len}자). 파일 확인: {content_path}")

    return draft


def load_published() -> list[dict]:
    with open(PUBLISHED_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_published(published: list[dict]) -> None:
    with open(PUBLISHED_PATH, "w", encoding="utf-8") as f:
        json.dump(published, f, ensure_ascii=False, indent=2)
        f.write("\n")


def run(draft_path: Path, status: str = "publish", skip_threads: bool = False) -> dict:
    draft = load_draft(draft_path)
    episode = draft["episode"]

    # 중복 발행 방지
    published = load_published()
    if any(p["ep"] == episode for p in published):
        raise SystemExit(f"이미 발행된 에피소드입니다: {episode}편 (published.json 확인)")

    # 1. WordPress 발행
    print(f"[1/4] WordPress 발행 중... ({episode}편: {draft['title']})")
    wp_result = publish_post(
        title=draft["title"],
        content=draft["content"],
        status=status,
        excerpt=draft["excerpt"],
        category_id=draft["category_id"],
        seo_title=draft["seo_title"],
        meta_description=draft["meta_description"],
        focus_keyword=draft["focus_keyword"],
    )
    print(f"      완료: {wp_result['url']} (status={wp_result['status']})")

    result = {"wp": wp_result, "notion": None, "threads": None, "errors": []}

    # draft 상태면 이력·SNS는 건너뜀
    if status != "publish":
        print("      draft 상태이므로 이력 기록/Threads는 건너뜁니다.")
        return result

    # 2. published.json 갱신
    print("[2/4] published.json 갱신 중...")
    published.append({
        "ep": episode,
        "title": wp_result["title"],
        "url": wp_result["url"],
        "date": date.today().isoformat(),
    })
    save_published(published)
    print(f"      완료: 총 {len(published)}편")

    # 3. Notion 기록 (실패해도 계속)
    print("[3/4] Notion 대시보드 기록 중...")
    try:
        result["notion"] = log_to_dashboard(
            title=wp_result["title"],
            category=draft["category"],
            url=wp_result["url"],
            threads=not skip_threads,
        )
        print("      완료")
    except Exception as e:
        result["errors"].append(f"Notion 기록 실패: {e}")
        print(f"      실패 (발행은 성공): {e}")

    # 4. Threads 포스팅 (실패해도 계속)
    if skip_threads:
        print("[4/4] Threads 건너뜀 (--skip-threads)")
    else:
        print("[4/4] Threads 포스팅 중...")
        try:
            result["threads"] = post_to_threads(
                text=draft["threads_text"],
                url=wp_result["url"],
            )
            print(f"      완료: {result['threads']['url']}")
        except Exception as e:
            result["errors"].append(f"Threads 포스팅 실패: {e}")
            print(f"      실패 (발행은 성공): {e}")

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="드래프트 파일을 WordPress에 발행합니다.")
    parser.add_argument("draft", help="드래프트 JSON 경로 (예: drafts/ep23.json)")
    parser.add_argument("--draft", dest="as_draft", action="store_true",
                        help="WP에 draft 상태로만 올림 (이력/Threads 생략)")
    parser.add_argument("--skip-threads", action="store_true", help="Threads 포스팅 생략")
    args = parser.parse_args()

    draft_path = Path(args.draft)
    if not draft_path.exists():
        sys.exit(f"드래프트 파일 없음: {draft_path}")

    result = run(
        draft_path,
        status="draft" if args.as_draft else "publish",
        skip_threads=args.skip_threads,
    )

    print("\n===== 발행 결과 =====")
    print(f"URL: {result['wp']['url']}")
    if result["threads"]:
        print(f"Threads: {result['threads']['url']}")
    for err in result["errors"]:
        print(f"⚠️ {err}")


if __name__ == "__main__":
    main()
