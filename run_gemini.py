import datetime
import sys
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox

import markdown
from tkcalendar import DateEntry

# 윈도우 환경에서 특수 기호나 다국어 출력 시 발생하는 인코딩(cp949) 오류 방지
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.trading_graph import TradingAgentsGraph

# 자주 검색하는 한글 종목명을 티커 코드로 자동 변환해주는 사전
KOREAN_TICKER_MAP = {
    # 국내 주요 주식 (KOSPI / KOSDAQ)
    "삼성전자": "005930.KS",
    "삼성전자우": "005935.KS",
    "SK하이닉스": "000660.KS",
    "하이닉스": "000660.KS",
    "LG에너지솔루션": "373220.KS",
    "엔솔": "373220.KS",
    "삼성바이오로직스": "207940.KS",
    "삼바": "207940.KS",
    "현대차": "005380.KS",
    "현대자동차": "005380.KS",
    "기아": "000270.KS",
    "셀트리온": "068270.KS",
    "KB금융": "105560.KS",
    "신한지주": "055550.KS",
    "POSCO홀딩스": "005490.KS",
    "포스코": "005490.KS",
    "포스코홀딩스": "005490.KS",
    "NAVER": "035420.KS",
    "네이버": "035420.KS",
    "카카오": "035720.KS",
    "에코프로비엠": "247540.KQ",
    "에코프로": "086520.KQ",
    "알테오젠": "196170.KQ",

    # 해외 주요 주식 (미국)
    "엔비디아": "NVDA",
    "애플": "AAPL",
    "테슬라": "TSLA",
    "마이크로소프트": "MSFT",
    "구글": "GOOGL",
    "알파벳": "GOOGL",
    "아마존": "AMZN",
    "메타": "META",

    # 가상자산 (코인)
    "비트코인": "BTC-USD",
    "이더리움": "ETH-USD",
    "리플": "XRP-USD",
    "솔라나": "SOL-USD",
}

# 티커 코드로 한글 이름을 찾기 위한 역방향 사전
TICKER_TO_KOREAN_MAP = {
    "005930.KS": "삼성전자",
    "005935.KS": "삼성전자우",
    "000660.KS": "SK하이닉스",
    "373220.KS": "LG에너지솔루션",
    "207940.KS": "삼성바이오로직스",
    "005380.KS": "현대차",
    "000270.KS": "기아",
    "068270.KS": "셀트리온",
    "105560.KS": "KB금융",
    "055550.KS": "신한지주",
    "005490.KS": "POSCO홀딩스",
    "035420.KS": "NAVER",
    "035720.KS": "카카오",
    "247540.KQ": "에코프로비엠",
    "086520.KQ": "에코프로",
    "196170.KQ": "알테오젠",
    "NVDA": "엔비디아",
    "AAPL": "애플",
    "TSLA": "테슬라",
    "MSFT": "마이크로소프트",
    "GOOGL": "구글",
    "AMZN": "아마존",
    "META": "메타",
    "BTC-USD": "비트코인",
    "ETH-USD": "이더리움",
    "XRP-USD": "리플",
    "SOL-USD": "솔라나",
}


def convert_to_valid_ticker(raw_input: str) -> tuple[str, str]:
    """사용자가 입력한 종목명을 (티커코드, 한글종목명) 튜플로 변환"""
    cleaned = raw_input.strip()

    if cleaned in KOREAN_TICKER_MAP:
        ticker = KOREAN_TICKER_MAP[cleaned]
        return ticker, cleaned

    if cleaned.isdigit() and len(cleaned) == 6:
        ticker = f"{cleaned}.KS"
        kor_name = TICKER_TO_KOREAN_MAP.get(ticker, "")
        return ticker, kor_name

    ticker = cleaned.upper()
    kor_name = TICKER_TO_KOREAN_MAP.get(ticker, "")
    return ticker, kor_name


def get_display_name(ticker: str, kor_name: str) -> str:
    """폴더명 및 보고서 표기용 이름 생성 (예: '005930.KS(삼성전자)' 또는 'NVDA(엔비디아)')"""
    if kor_name:
        return f"{ticker}({kor_name})"
    return ticker


def get_user_inputs():
    """사용자가 종목을 입력하고 달력에서 날짜를 마우스로 고를 수 있는 입력창 팝업"""
    if len(sys.argv) >= 3:
        ticker, kor_name = convert_to_valid_ticker(sys.argv[1])
        return ticker, kor_name, sys.argv[2].strip()
    elif len(sys.argv) == 2:
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        ticker, kor_name = convert_to_valid_ticker(sys.argv[1])
        return ticker, kor_name, today_str

    selected_inputs = {"ticker": "005930.KS", "kor_name": "삼성전자", "date": "2026-09-01", "submitted": False}

    root = tk.Tk()
    root.title("TradingAgents - 종목 및 기준일 선택")
    root.geometry("440x290")
    root.resizable(False, False)

    root.update_idletasks()
    x = (root.winfo_screenwidth() - 440) // 2
    y = (root.winfo_screenheight() - 290) // 2
    root.geometry(f"440x290+{x}+{y}")

    header = tk.Label(
        root,
        text="📊 분석할 종목과 기준일을 선택하세요",
        font=("Malgun Gothic", 12, "bold"),
        pady=10
    )
    header.pack()

    frame = tk.Frame(root, padx=20, pady=5)
    frame.pack(fill="x")

    tk.Label(
        frame,
        text="종목명 또는 티커:",
        font=("Malgun Gothic", 10, "bold")
    ).grid(row=0, column=0, sticky="w", pady=8)

    ticker_entry = tk.Entry(frame, font=("Malgun Gothic", 10), width=20)
    ticker_entry.insert(0, "삼성전자")
    ticker_entry.grid(row=0, column=1, pady=8, padx=10)

    tk.Label(
        frame,
        text="💡 '삼성전자', '005930.KS', 'NVDA', '테슬라' 모두 입력 가능!",
        font=("Malgun Gothic", 8),
        fg="#2563EB"
    ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 5))

    tk.Label(
        frame,
        text="분석 기준일 (달력):",
        font=("Malgun Gothic", 10, "bold")
    ).grid(row=2, column=0, sticky="w", pady=10)

    cal_entry = DateEntry(
        frame,
        width=18,
        background="#1E40AF",
        foreground="white",
        borderwidth=2,
        date_pattern="yyyy-mm-dd",
        font=("Malgun Gothic", 10)
    )
    cal_entry.grid(row=2, column=1, pady=10, padx=10)

    def on_submit():
        raw_val = ticker_entry.get().strip()
        if not raw_val:
            messagebox.showwarning("입력 확인", "종목명을 입력해주세요!")
            return

        ticker, kor_name = convert_to_valid_ticker(raw_val)

        import re
        if re.search(r"[ㄱ-ㅎㅏ-ㅣ가-힣]", ticker):
            messagebox.showerror(
                "티커 코드 필요",
                f"'{raw_val}'의 티커 코드를 찾을 수 없습니다.\n\n"
                "한국 주식은 6자리 숫자(예: 005930 또는 005930.KS)\n"
                "해외 주식은 영문 티커(예: NVDA, TSLA)로 입력해주세요!"
            )
            return

        selected_inputs["ticker"] = ticker
        selected_inputs["kor_name"] = kor_name
        selected_inputs["date"] = cal_entry.get_date().strftime("%Y-%m-%d")
        selected_inputs["submitted"] = True
        root.destroy()

    btn_submit = tk.Button(
        root,
        text="🚀 AI 분석 시작",
        font=("Malgun Gothic", 11, "bold"),
        bg="#2563EB",
        fg="white",
        padx=15,
        pady=6,
        relief="raised",
        cursor="hand2",
        command=on_submit
    )
    btn_submit.pack(pady=12)

    root.mainloop()

    if not selected_inputs["submitted"]:
        print("\n[안내] 창이 닫혀 기본 설정(005930.KS(삼성전자), 2026-09-01)으로 진행합니다.")

    return selected_inputs["ticker"], selected_inputs["kor_name"], selected_inputs["date"]


def save_html_report(md_content: str, display_name: str, trade_date: str, decision: str, save_path: Path, memory_path: Path) -> Path:
    """마크다운 보고서 내용을 웹 브라우저에서 바로 볼 수 있는 깔끔한 HTML 파일로 저장"""
    decision_str = str(decision).upper()
    if "BUY" in decision_str:
        badge_bg, badge_text = "#16A34A", "매수 (BUY)"
    elif "SELL" in decision_str:
        badge_bg, badge_text = "#DC2626", "매도 (SELL)"
    else:
        badge_bg, badge_text = "#D97706", "관망 / 보유 (HOLD)"

    html_body = markdown.markdown(md_content, extensions=["tables", "fenced_code", "nl2br"])

    html_full = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>트레이딩 분석 리포트 - {display_name}</title>
    <style>
        :root {{
            --bg: #F8FAFC;
            --card-bg: #FFFFFF;
            --text-main: #1E293B;
            --text-sub: #64748B;
            --primary: #2563EB;
            --border: #E2E8F0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Malgun Gothic", sans-serif;
            background-color: var(--bg);
            color: var(--text-main);
            line-height: 1.7;
            margin: 0;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 960px;
            margin: 0 auto;
        }}
        .header-card {{
            background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
            color: white;
            border-radius: 16px;
            padding: 32px;
            margin-bottom: 24px;
            box-shadow: 0 10px 25px -5px rgba(37, 99, 235, 0.2);
        }}
        .header-card h1 {{
            margin: 0 0 10px 0;
            font-size: 28px;
            font-weight: 800;
        }}
        .header-meta {{
            font-size: 15px;
            opacity: 0.95;
            margin-bottom: 20px;
        }}
        .decision-badge {{
            display: inline-block;
            background-color: {badge_bg};
            color: white;
            padding: 8px 20px;
            border-radius: 30px;
            font-size: 16px;
            font-weight: 700;
            letter-spacing: 0.5px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        }}
        .pro-tip-card {{
            background: #F0FDF4;
            border: 1px solid #BBF7D0;
            border-radius: 16px;
            padding: 24px 28px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        }}
        .pro-tip-card h3 {{
            color: #15803D;
            margin: 0 0 10px 0;
            font-size: 18px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .pro-tip-card p {{
            margin: 6px 0;
            font-size: 14.5px;
            color: #166534;
            line-height: 1.6;
        }}
        .pro-tip-card code {{
            background-color: #DCFCE7;
            color: #14532D;
            padding: 2px 8px;
            border-radius: 4px;
            font-weight: 600;
            font-family: Consolas, monospace;
        }}
        .content-card {{
            background: var(--card-bg);
            border-radius: 16px;
            padding: 40px;
            border: 1px solid var(--border);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }}
        h2 {{
            color: #1E3A8A;
            border-bottom: 2px solid #DBEAFE;
            padding-bottom: 10px;
            margin-top: 36px;
            font-size: 22px;
        }}
        h3 {{
            color: #2563EB;
            margin-top: 24px;
            font-size: 18px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 14px;
        }}
        th, td {{
            padding: 12px 14px;
            border: 1px solid var(--border);
            text-align: left;
        }}
        th {{
            background-color: #F1F5F9;
            color: #334155;
            font-weight: 600;
        }}
        tr:nth-child(even) {{
            background-color: #F8FAFC;
        }}
        pre, code {{
            background-color: #F1F5F9;
            color: #0F172A;
            border-radius: 6px;
            font-family: Consolas, monospace;
        }}
        pre {{
            padding: 16px;
            overflow-x: auto;
        }}
        blockquote {{
            border-left: 4px solid var(--primary);
            margin: 16px 0;
            padding: 8px 16px;
            background-color: #EFF6FF;
            color: #1E40AF;
        }}
        .footer {{
            text-align: center;
            color: var(--text-sub);
            font-size: 13px;
            margin-top: 40px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header-card">
            <h1>📈 AI 종합 트레이딩 분석 리포트</h1>
            <div class="header-meta">
                <strong>분석 종목:</strong> {display_name} &nbsp;|&nbsp;
                <strong>분석 기준일:</strong> {trade_date} &nbsp;|&nbsp;
                <strong>리포트 생성 시각:</strong> {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            </div>
            <div>
                <span class="decision-badge">최종 판단: {badge_text}</span>
            </div>
        </div>

        <!-- 실무 활용 포인트 카드 -->
        <div class="pro-tip-card">
            <h3>💡 실무 활용 포인트: 디시전 로그(trading_memory.md) 추적 및 Reflection</h3>
            <p><strong>• 메모리 로그 파일:</strong> <code>{memory_path}</code></p>
            <p><strong>• 자가 학습 원리:</strong> 위 경로에 이번 판단 결과가 자동으로 기록되며, 실제 매매 후 실현 수익률(Realised Alpha)을 입력하면 Gemini가 <strong>과거 실수를 스스로 반성(Reflection)</strong>합니다.</p>
            <p><strong>• 정밀도 향상:</strong> 실행을 거듭할수록 Gemini가 과거의 오판과 성공 경험을 프롬프트에 자동으로 불러와 <strong>판단 정밀도가 지속적으로 향상</strong>됩니다.</p>
        </div>

        <div class="content-card">
            {html_body}
        </div>

        <div class="footer">
            Generated by TradingAgents (Gemini Multi-Agent System) • 본 리포트는 AI 분석 참고용 자료입니다.
        </div>
    </div>
</body>
</html>
"""
    html_file = save_path / "report.html"
    html_file.write_text(html_full, encoding="utf-8")
    return html_file


if __name__ == "__main__":
    # ==============================================================================
    # 1. 사용자 입력 받기 (달력 팝업 창)
    # ==============================================================================
    target_ticker, target_kor_name, target_date = get_user_inputs()
    display_name = get_display_name(target_ticker, target_kor_name)

    print(f"\n▶ 선택된 분석 종목: {display_name}")
    print(f"▶ 선택된 분석 기준일: {target_date}\n")

    # ==============================================================================
    # 2. [vibe-local-info 모델 우선순위 및 한국어 설정]
    # ==============================================================================
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = "google"

    # 모든 리포트 및 최종 의사결정을 한국어로 출력하도록 설정
    config["output_language"] = "Korean"

    # vibe-local-info 우선순위 적용:
    # 1순위: 'gemini-3.5-flash-lite' (RPM 15, RPD 500 - 빠른 데이터 파싱 및 개별 분석)
    # 3순위: 'gemini-3.5-flash'      (종합 토론 및 심층 추론)
    config["quick_think_llm"] = "gemini-3.5-flash-lite"
    config["deep_think_llm"] = "gemini-3.5-flash"

    # 메모리 로그 저장 위치를 현재 프로젝트(에이전트) 폴더의 memory/trading_memory.md 로 고정
    project_root = Path(__file__).resolve().parent
    local_memory_path = project_root / "memory" / "trading_memory.md"
    local_memory_path.parent.mkdir(parents=True, exist_ok=True)
    config["memory_log_path"] = str(local_memory_path)

    # ==============================================================================
    # 3. 트레이딩 에이전트 그래프 인스턴스 초기화 및 실행
    # ==============================================================================
    ta = TradingAgentsGraph(debug=True, config=config)

    final_state, decision = ta.propagate(target_ticker, target_date)
    print("\n=== 최종 트레이딩 의사결정 ===")
    print(decision)

    # ==============================================================================
    # 4. 웹 브라우저(HTML) 형식의 리포트 파일 생성 및 자동 열기
    # 예: reports/005930.KS(삼성전자)_2026-09-10_230614/report.html
    # ==============================================================================
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    report_folder_name = f"{display_name}_{target_date}_{timestamp}"
    report_dir = Path("reports") / report_folder_name
    report_dir.mkdir(parents=True, exist_ok=True)

    # 메모리 로그 경로
    memory_file_path = local_memory_path

    # 종합 마크다운 보고서 저장
    md_file = ta.save_reports(final_state, target_ticker, report_dir)

    # 웹 브라우저용 HTML 보고서 생성 (실무 활용 포인트 카드 포함)
    md_text = md_file.read_text(encoding="utf-8")
    html_file = save_html_report(md_text, display_name, target_date, decision, report_dir, memory_file_path)

    print("\n" + "=" * 65)
    print("📄 [리포트 파일 저장 완료]")
    print(f" - 저장 폴더: {report_dir.resolve()}")
    print(f" - 마크다운: {md_file.name}")
    print(f" - 웹 브라우저 리포트: {html_file.name}")
    print("=" * 65)
    print("💡 [실무 활용 포인트: 디시전 로그(trading_memory.md) 추적]")
    print(f" - 저장 위치: {memory_file_path}")
    print(" - 이번 판단 결과가 누적되었으며, 실제 매매 후 실현 수익률을")
    print("   반영(Reflection)하면 실행을 거듭할수록 Gemini의 판단 정밀도가 높아집니다.")
    print("=" * 65)

    # 기본 웹 브라우저로 리포트 자동 열기
    try:
        webbrowser.open(html_file.resolve().as_uri())
        print("\n🌐 웹 브라우저에서 리포트를 자동으로 열었습니다!")
    except Exception as e:
        print(f"\n[안내] 브라우저 자동 실행 실패: {e}")

    # ==============================================================================
    # 5. deep-dive-lounge 웹사이트(블로그/정적 리포트)로 자동 내보내기
    # ==============================================================================
    try:
        from export_to_lounge import export_report_to_lounge
        lounge_path = Path(r"d:\Data\_Vibe-Coding\deep-dive-lounge")
        if lounge_path.exists():
            exp_res = export_report_to_lounge(report_dir, lounge_path)
            print("\n" + "=" * 65)
            print("🚀 [deep-dive-lounge 웹사이트 자동 업로드 완료!]")
            print(f" - 블로그 포스트: {exp_res['post_path'].name}")
            print(f" - 웹 리포트 상대주소: {exp_res['web_url']}")
            print("=" * 65)
    except Exception as exp_err:
        print(f"\n[안내] deep-dive-lounge 자동 업로드 건너뜀: {exp_err}")

    # ==============================================================================
    # 5. [실무 팁] 실제 매매 후 실현 수익률 반성(Reflection) 실행 방법 예시
    # 나중에 실제 수익률(예: +5.2% 이면 5.2, -3.0% 이면 -3.0)이 확정되었을 때
    # 아래 주석을 해제하고 실행하시면 Gemini가 과거 판단을 회고하고 메모리에 저장합니다:
    # ------------------------------------------------------------------------------
    # realized_return = 5.2   # 예: 포지션 청산 후 실현 수익률 (%)
    # ta.reflect_and_remember(realized_return)
    # print(f"✨ 과거 판단 회고(Reflection)가 {memory_file_path}에 기록되었습니다!")
    # ==============================================================================
