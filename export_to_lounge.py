import datetime
import re
import shutil
import sys
from pathlib import Path

# 실제 배포되는 Cloudflare Pages 기본 도메인
LOUNGE_BASE_URL = "https://deep-dive-lounge.pages.dev"


def export_report_to_lounge(report_dir_path: Path, lounge_root: Path = None) -> dict:
    """
    TradingAgents 분석 결과(report.html, complete_report.md)를
    deep-dive-lounge 웹사이트(https://deep-dive-lounge.pages.dev)의
    정적 리포트 및 블로그 게시글로 자동 내보내기
    """
    report_dir = Path(report_dir_path).resolve()
    if not report_dir.exists():
        raise FileNotFoundError(f"리포트 폴더를 찾을 수 없습니다: {report_dir}")

    # deep-dive-lounge 기본 경로 (로컬 또는 CI 환경)
    if lounge_root is None:
        env_lounge = Path(r"d:\Data\_Vibe-Coding\deep-dive-lounge")
        if env_lounge.exists():
            lounge_root = env_lounge
        else:
            # 깃허브 액션 환경 등에서 같은 상위 디렉토리에 클론된 경우
            sibling_lounge = Path("deep-dive-lounge")
            lounge_root = sibling_lounge if sibling_lounge.exists() else env_lounge

    lounge_root = Path(lounge_root).resolve()
    if not lounge_root.exists():
        raise FileNotFoundError(f"deep-dive-lounge 프로젝트 폴더를 찾을 수 없습니다: {lounge_root}")

    folder_name = report_dir.name
    # 예: 005380.KS(현대자동차)_2026-09-10_20260910_160143
    html_file = report_dir / "report.html"
    md_file = report_dir / "complete_report.md"

    if not html_file.exists():
        raise FileNotFoundError(f"report.html 파일이 없습니다: {html_file}")

    # =========================================================================
    # 1. deep-dive-lounge/public/reports/{folder_name} 에 정적 파일 복사
    # =========================================================================
    public_reports_dir = lounge_root / "public" / "reports" / folder_name
    public_reports_dir.mkdir(parents=True, exist_ok=True)

    shutil.copytree(report_dir, public_reports_dir, dirs_exist_ok=True)
    web_relative_url = f"/reports/{folder_name}/report.html"
    web_absolute_url = f"{LOUNGE_BASE_URL}{web_relative_url}"

    # =========================================================================
    # 2. deep-dive-lounge/src/content/posts 에 블로그 포스트(.md) 자동 생성
    # =========================================================================
    posts_dir = lounge_root / "src" / "content" / "posts"
    posts_dir.mkdir(parents=True, exist_ok=True)

    # 폴더명에서 종목 정보 및 날짜 추출
    parts = folder_name.split("_")
    display_name = parts[0] if len(parts) >= 1 else "주식분석"
    trade_date = parts[1] if len(parts) >= 2 else datetime.date.today().strftime("%Y-%m-%d")

    # 슬러그 생성 (영문/숫자/하이픈)
    safe_slug_ticker = re.sub(r"[^a-zA-Z0-9]", "-", display_name).strip("-").lower()
    timestamp_slug = parts[2] if len(parts) >= 3 else datetime.datetime.now().strftime("%H%M%S")
    slug = f"{trade_date}-{safe_slug_ticker}-{timestamp_slug}"

    md_content = md_file.read_text(encoding="utf-8") if md_file.exists() else ""

    # 투자의견 추출
    decision_match = re.search(r"FINAL TRANSACTION PROPOSAL:\s*\*\*?(BUY|HOLD|SELL)\*\*?", md_content, re.IGNORECASE)
    decision_text = decision_match.group(1).upper() if decision_match else "HOLD"

    title = f"[{decision_text}] {display_name} AI 심층 트레이딩 분석 리포트"
    summary = f"Gemini 멀티 에이전트(시장·뉴스·재무·토론)가 도출한 {display_name}의 투자 의사결정({decision_text}) 및 심층 분석 리포트입니다."

    # 블로그용 Frontmatter 마크다운 생성
    blog_post_content = f"""---
title: "{title}"
date: "{trade_date}"
summary: "{summary}"
category: "AI 주식 분석"
tags: ["AI주식분석", "{display_name}", "{decision_text}", "TradingAgents"]
---

> 📊 **[👉 전체 웹 브라우저 상세 리포트 새 창으로 열기]({web_absolute_url})**
>
> *본 리포트는 Google Gemini 멀티 에이전트 기반 금융 분석 시스템이 자동으로 작성한 분석 보고서입니다.*

---

## 🎯 최종 투자 의사결정 요약
- **분석 종목:** `{display_name}`
- **분석 기준일:** `{trade_date}`
- **AI 최종 판단:** **`{decision_text}`**

---

{md_content}

---
*Generated automatically by TradingAgents for Deep Dive Lounge ({LOUNGE_BASE_URL})*
"""

    post_file = posts_dir / f"{slug}.md"
    post_file.write_text(blog_post_content, encoding="utf-8")

    return {
        "web_url": web_relative_url,
        "full_url": web_absolute_url,
        "public_path": public_reports_dir,
        "post_path": post_file,
        "slug": slug,
    }


if __name__ == "__main__":
    # 특정 폴더 경로 인자가 주어진 경우
    target_report_dir = None
    target_lounge_dir = None

    if len(sys.argv) >= 2:
        target_report_dir = Path(sys.argv[1])
    if len(sys.argv) >= 3:
        target_lounge_dir = Path(sys.argv[2])

    if target_report_dir is None:
        reports_base = Path("reports")
        if not reports_base.exists():
            print("[안내] 아직 생성된 reports 폴더가 없습니다.")
            sys.exit(0)

        subdirs = sorted([d for d in reports_base.iterdir() if d.is_dir()], key=lambda d: d.stat().st_mtime, reverse=True)
        if not subdirs:
            print("[안내] 내보낼 리포트 폴더가 없습니다.")
            sys.exit(0)

        target_report_dir = subdirs[0]

    print(f"▶ 대상 리포트: {target_report_dir.name}")
    res = export_report_to_lounge(target_report_dir, target_lounge_dir)

    print("\n" + "=" * 65)
    print("🚀 [deep-dive-lounge 웹사이트 업로드 완료!]")
    print(f" - 정적 웹 리포트 복사: {res['public_path']}")
    print(f" - 블로그 게시글 생성: {res['post_path']}")
    print(f" - 배포 웹 접속 주소: {res['full_url']}")
    print("=" * 65)
