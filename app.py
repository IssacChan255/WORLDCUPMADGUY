"""2026 World Cup MD1 — 6/18 four-match prediction dashboard."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA_PATH = Path(__file__).resolve().parent / "matches.json"
OUTCOME_ZH = {"home": "主胜", "draw": "平局", "away": "客胜"}


@st.cache_data
def load_data() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def match_date_label(match: dict) -> str:
    """下拉选项：以开球日期时间为主标签。"""
    return match["kickoff"]


def match_lookup(data: dict) -> dict[str, dict]:
    return {match_date_label(m): m for m in data["matches"]}


def _apply_bar_chart_layout(
    fig: go.Figure,
    y_values: list[float],
    *,
    height: int = 300,
    top_margin: int = 55,
    y_pad: float = 0.35,
) -> go.Figure:
    ymax = max(y_values) if y_values else 0.1
    fig.update_layout(
        height=height,
        margin=dict(l=20, r=20, t=top_margin, b=20),
        yaxis=dict(range=[0, ymax * (1 + y_pad)]),
        uniformtext_minsize=8,
        uniformtext_mode="hide",
    )
    fig.update_traces(cliponaxis=False, textposition="outside")
    return fig


def prob_comparison_figure(match: dict) -> go.Figure:
    model = match["result_analysis"]["probabilities"]
    market = match["market_implied"]
    labels = ["主胜", "平局", "客胜"]
    model_vals = [model["home_win"], model["draw"], model["away_win"]]
    market_vals = [market["home"], market["draw"], market["away"]]

    fig = go.Figure()
    fig.add_bar(name="模型", x=labels, y=model_vals, marker_color="#00c896")
    fig.add_bar(name="市场隐含", x=labels, y=market_vals, marker_color="#3b82f6", opacity=0.75)
    fig.update_layout(
        barmode="group",
        height=340,
        margin=dict(l=20, r=20, t=70, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.12, xanchor="center", x=0.5),
        yaxis=dict(tickformat=".0%", title="概率", range=[0, max(model_vals + market_vals) * 1.15]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def scorelines_figure(match: dict) -> go.Figure:
    scores = match["score_analysis"]["top_scorelines"]
    df = pd.DataFrame(scores)
    colors = ["#00c896" if i == 0 else "#64748b" for i in range(len(df))]
    fig = go.Figure(go.Bar(
        x=df["score"],
        y=df["prob"],
        marker_color=colors,
        text=[pct(p) for p in df["prob"]],
        textposition="outside",
        cliponaxis=False,
    ))
    fig.update_layout(
        yaxis=dict(tickformat=".0%", title="Poisson 概率"),
        xaxis_title="比分",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return _apply_bar_chart_layout(fig, df["prob"].tolist(), height=340, top_margin=60)


def xg_figure(match: dict) -> go.Figure:
    sc = match["score_analysis"]
    home = sc["expected_goals"]["home"]
    away = sc["expected_goals"]["away"]
    fig = go.Figure(go.Bar(
        x=[match["team_analysis"]["home"]["display"], match["team_analysis"]["away"]["display"]],
        y=[home, away],
        marker_color=["#22c55e", "#60a5fa"],
        text=[f"{home:.2f}", f"{away:.2f}"],
        textposition="outside",
        cliponaxis=False,
    ))
    fig.update_layout(
        yaxis_title="期望进球 xG",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return _apply_bar_chart_layout(fig, [home, away], height=300, top_margin=55)


def render_overview(data: dict) -> None:
    rows = []
    for m in data["matches"]:
        rec = m["recommendation"]
        rows.append({
            "开球": m["kickoff"],
            "比赛": m["title"],
            "模型": f"{rec['pick_1x2']} · {rec['pick_score']}",
            "市场": m["market_pick_zh"],
            "一致": "✓" if m["alignment"] == "high" else "≠",
            "xG合计": m["score_analysis"]["total_xg"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_match(match: dict) -> None:
    rec = match["recommendation"]
    res = match["result_analysis"]
    sc = match["score_analysis"]
    odds = match["market_odds"]

    align = "模型与市场方向一致" if match["alignment"] == "high" else "模型与市场存在分歧"
    st.caption(f"{match['group']}组 · {match['kickoff']} · {align}")

    c1, c2, c3 = st.columns(3)
    c1.metric("模型推荐", f"{rec['pick_1x2']} · {rec['pick_score']}", pct(rec["pick_1x2_prob"]))
    c2.metric("市场倾向", match["market_pick_zh"], f"主 {pct(match['market_implied']['home'])}")
    c3.metric("xG 合计", f"{sc['total_xg']:.2f}", sc["total_goals_tendency"])

    st.info(rec["summary"])

    left, right = st.columns(2)
    with left:
        st.plotly_chart(prob_comparison_figure(match), use_container_width=True)
    with right:
        st.plotly_chart(scorelines_figure(match), use_container_width=True)

    st.plotly_chart(xg_figure(match), use_container_width=True)

    o1, o2, o3 = st.columns(3)
    o1.metric("主胜赔率", odds["home"])
    o2.metric("平局赔率", odds["draw"])
    o3.metric("客胜赔率", odds["away"])

    tab1, tab2, tab3 = st.tabs(["胜负依据", "比分依据", "球队分析"])
    with tab1:
        for r in res["reasons"]:
            st.markdown(f"**{r['factor']}**（{r['weight']}）  \n{r['detail']}")
    with tab2:
        for r in sc.get("score_reasons", []):
            st.markdown(f"**{r['factor']}** → {r['supports']}  \n{r['detail']}")
        for line in sc.get("prep_impact_summary", []):
            st.caption(line)
    with tab3:
        t1, t2 = st.columns(2)
        for col, side in ((t1, "home"), (t2, "away")):
            t = match["team_analysis"][side]
            with col:
                st.subheader(t["display"])
                st.write(f"Elo **{t['elo']}** · {t['coach']}（{t['coach_style']}）")
                if t.get("strengths"):
                    st.success("优势: " + "；".join(t["strengths"]))
                if t.get("weaknesses"):
                    st.warning("隐患: " + "；".join(t["weaknesses"]))
                for note in t.get("notes", [])[:6]:
                    st.write(f"- {note}")

    with st.expander("备战周期 / 战意参考"):
        st.text(match.get("prep_text", ""))


def main() -> None:
    st.set_page_config(
        page_title="WC2026 · 6/18 预测",
        page_icon="⚽",
        layout="wide",
    )
    data = load_data()

    st.title("2026 世界杯 · 小组赛 MD1 预测看板")
    st.markdown(f"**{data['model']}** · 生成日期 {data['generated']}")

    date_labels = [match_date_label(m) for m in data["matches"]]
    by_date = match_lookup(data)
    view = st.sidebar.radio("视图", ["总览", "单场详情"], index=0)
    selected_date = st.sidebar.selectbox("选择比赛", date_labels, index=0)
    selected_match = by_date[selected_date]

    if view == "总览":
        render_overview(data)
        st.divider()
        for m in data["matches"]:
            expander_label = f"{match_date_label(m)} · {m['title']}"
            with st.expander(expander_label, expanded=match_date_label(m) == selected_date):
                render_match(m)
    else:
        st.header(selected_match["title"])
        st.caption(f"开球时间 {selected_date}")
        render_match(selected_match)

    st.sidebar.divider()
    st.sidebar.caption("数据仅供研究参考，不构成投注建议。")


if __name__ == "__main__":
    main()
