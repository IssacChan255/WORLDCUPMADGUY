"""世界杯主题样式与页头组件。"""
from __future__ import annotations

WC_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;600;700;800&display=swap');

  html, body, [class*="css"] {
    font-family: "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif !important;
  }

  .block-container {
    padding-top: 1rem;
    padding-bottom: 2.5rem;
    max-width: 1100px;
  }

  .wc-hero {
    position: relative;
    overflow: hidden;
    border-radius: 18px;
    padding: 1.35rem 1.4rem 1.2rem;
    margin-bottom: 1.1rem;
    background: linear-gradient(125deg, #0b1f3a 0%, #123d2e 42%, #1a4d8c 100%);
    border: 1px solid #2a5a8a55;
    box-shadow: 0 12px 40px #00000055;
  }
  .wc-hero::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
      repeating-linear-gradient(
        90deg,
        transparent,
        transparent 38px,
        rgba(255,255,255,0.025) 38px,
        rgba(255,255,255,0.025) 76px
      );
    pointer-events: none;
  }
  .wc-hero .badge {
    display: inline-block;
    font-size: 0.72rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #fcd34d;
    border: 1px solid #fcd34d66;
    border-radius: 999px;
    padding: 0.15rem 0.65rem;
    margin-bottom: 0.45rem;
  }
  .wc-hero h1 {
    margin: 0;
    font-size: 1.65rem;
    font-weight: 800;
    color: #fff;
    line-height: 1.25;
  }
  .wc-hero .sub {
    margin-top: 0.45rem;
    color: #c8daf0;
    font-size: 0.92rem;
  }
  .wc-hero .stats {
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
    margin-top: 0.85rem;
  }
  .wc-stat-pill {
    background: rgba(255,255,255,0.08);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 10px;
    padding: 0.35rem 0.7rem;
    font-size: 0.82rem;
    color: #e8f0ff;
  }
  .wc-stat-pill strong { color: #6ee7b7; }

  .group-card {
    background: linear-gradient(180deg, #162032 0%, #121a28 100%);
    border: 1px solid #2a3f5f;
    border-radius: 14px;
    padding: 0.85rem 0.9rem 0.75rem;
    margin-bottom: 0.75rem;
    height: 100%;
  }
  .group-card .group-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.55rem;
    padding-bottom: 0.45rem;
    border-bottom: 1px solid #2a3f5f;
  }
  .group-card .group-letter {
    font-size: 1.15rem;
    font-weight: 800;
    color: #fcd34d;
  }
  .group-card .group-meta {
    font-size: 0.75rem;
    color: #8b9bb8;
  }

  .standings-row {
    display: grid;
    grid-template-columns: 1.4rem 1fr auto;
    gap: 0.35rem 0.5rem;
    align-items: center;
    padding: 0.32rem 0.35rem;
    border-radius: 8px;
    font-size: 0.84rem;
    color: #d7e3f4;
  }
  .standings-row.q { background: rgba(16, 185, 129, 0.12); border-left: 3px solid #10b981; }
  .standings-row.t { background: rgba(245, 158, 11, 0.10); border-left: 3px solid #f59e0b; }
  .standings-row.e { opacity: 0.72; }
  .standings-row .rk { color: #8b9bb8; font-weight: 700; text-align: center; }
  .standings-row .pts { font-weight: 700; color: #6ee7b7; min-width: 1.6rem; text-align: right; }
  .standings-row .rec { color: #8b9bb8; font-size: 0.75rem; }

  .outlook-card {
    background: #121a28;
    border: 1px solid #2a3f5f;
    border-radius: 12px;
    padding: 0.75rem 0.85rem;
    margin-bottom: 0.55rem;
  }
  .outlook-card .team { font-weight: 700; color: #f0f4ff; font-size: 0.95rem; }
  .outlook-card .path { color: #6ee7b7; font-size: 0.84rem; margin-top: 0.2rem; }
  .outlook-card .note { color: #8b9bb8; font-size: 0.78rem; margin-top: 0.15rem; }

  .pick-hero {
    background: linear-gradient(135deg, #1a2332 0%, #121a2b 100%);
    border: 1px solid #243049;
    border-radius: 14px;
    padding: 1rem 1.15rem;
    margin-bottom: 0.75rem;
  }
  .pick-hero .title { color: #8b9bb8; font-size: 0.82rem; margin-bottom: 0.25rem; }
  .pick-hero .main { color: #00c896; font-size: 1.55rem; font-weight: 700; }
  .pick-hero .sub { color: #c5d0e6; font-size: 0.92rem; margin-top: 0.35rem; }
  .tag-row { display: flex; flex-wrap: wrap; gap: 0.4rem; margin: 0.5rem 0 0.2rem; }
  .tag {
    font-size: 0.75rem; padding: 0.15rem 0.55rem; border-radius: 999px;
    border: 1px solid #243049; background: #ffffff08; color: #8b9bb8;
  }
  .tag.ok { color: #00c896; border-color: #00c89655; }
  .tag.warn { color: #f59e0b; border-color: #f59e0b55; }
  .tag.bad { color: #ef4444; border-color: #ef444455; }

  [data-testid="stMetricValue"] { font-size: 1.35rem; }

  div[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0e1624 0%, #121a28 100%);
  }

  @media (max-width: 640px) {
    [data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; min-width: 100% !important; }
    .wc-hero h1 { font-size: 1.35rem; }
  }
</style>
"""


def render_wc_hero(*, title: str, subtitle: str, pills: list[tuple[str, str]]) -> None:
    import streamlit as st

    pills_html = "".join(
        f'<span class="wc-stat-pill">{label} <strong>{value}</strong></span>'
        for label, value in pills
    )
    st.markdown(
        f"""
<div class="wc-hero">
  <div class="badge">FIFA WORLD CUP 2026</div>
  <h1>{title}</h1>
  <div class="sub">{subtitle}</div>
  <div class="stats">{pills_html}</div>
</div>
        """,
        unsafe_allow_html=True,
    )


def inject_wc_styles() -> None:
    import streamlit as st

    st.markdown(WC_CSS, unsafe_allow_html=True)
