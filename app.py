"""2026 世界杯小组赛预测看板（Streamlit · 全中文详解）。"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from ui_standings import load_standings, render_standings_dashboard
from ui_theme import inject_wc_styles, render_wc_hero
from ui_zh import (
    ALIGNMENT_ZH,
    DRAW_RULE_ZH,
    GOALS_TENDENCY_ZH,
    zh_injury_bundle,
    zh_insights,
    zh_model_label,
    zh_reason,
    zh_summary,
    zh_team_notes,
    zh_text,
)

DATA_PATH = Path(__file__).resolve().parent / "matches.json"


@st.cache_data
def load_data() -> dict:
    return json.loads(DATA_PATH.read_text(encoding="utf-8"))


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def match_label(match: dict) -> str:
    return match["kickoff"]


def inject_styles() -> None:
    inject_wc_styles()


def match_groups(data: dict) -> list[str]:
    groups = sorted({m["group"] for m in data.get("matches", [])})
    return groups


def render_home_hero(data: dict) -> None:
    standings = load_standings()
    meta = standings.get("meta") or {}
    md1 = data.get("md1_total") or {}
    md2 = data.get("md2_preview") or {}
    pills = [
        ("已赛", f"{meta.get('results_count', md1.get('matches_played', '—'))} 场"),
        ("轮次", f"第 {meta.get('matchday', '—')} 轮"),
        ("本批", f"{len(data.get('matches', []))} 场预测"),
    ]
    if md2.get("kickoff"):
        pills.append(("焦点", f"{md2['kickoff']} A/B 组"))
    if md1.get("md1_backtest_1x2"):
        pills.append(("首轮回测", f"胜负 {md1['md1_backtest_1x2']}"))
    subtitle = data.get("batch_label") or f"数据更新于 {data.get('generated', '—')}"
    if md2.get("note"):
        subtitle = f"{subtitle} · {md2['note']}"
    render_wc_hero(
        title="2026 美加墨世界杯 · 小组赛预测看板",
        subtitle=subtitle,
        pills=pills,
    )


def render_pick_hero(match: dict) -> None:
    rec = match["recommendation"]
    align = ALIGNMENT_ZH.get(match.get("alignment", ""), "方向对照见下文")
    tendency = GOALS_TENDENCY_ZH.get(
        match["score_analysis"].get("total_goals_tendency", ""),
        match["score_analysis"].get("total_goals_tendency", ""),
    )
    st.markdown(
        f"""
<div class="pick-hero">
  <div class="title">{match['group']}组 · {match['kickoff']} · {zh_text(align)}</div>
  <div class="main">推荐 {rec['pick_1x2']} · {rec['pick_score']}</div>
  <div class="sub">胜平负置信度 {pct(rec['pick_1x2_prob'])} · 庄家倾向 {match['market_pick_zh']} · {tendency}</div>
</div>
        """,
        unsafe_allow_html=True,
    )
    tags = []
    if match.get("draw_pick_applied"):
        rule = DRAW_RULE_ZH.get(match.get("draw_pick_rule", ""), "平局专项规则")
        tags.append(("平局覆盖推荐", "warn"))
        tags.append((rule, "warn"))
    inj = match.get("injuries") or {}
    if inj.get("home", {}).get("players") or inj.get("away", {}).get("players"):
        tags.append(("有伤停情报", ""))
    net = inj.get("net_impact")
    if net is not None and abs(net) >= 0.1:
        tags.append((f"伤病差 {inj.get('net_label', '')}", "warn"))
    for note in match.get("score_analysis", {}).get("calibration_notes") or []:
        tags.append((zh_text(note), ""))
    if tags:
        html = '<div class="tag-row">' + "".join(
            f'<span class="tag {cls}">{t}</span>' for t, cls in tags
        ) + "</div>"
        st.markdown(html, unsafe_allow_html=True)


def prob_bars(match: dict) -> None:
    """纯中文概率条，窄屏比双柱图更易读。"""
    model = match["result_analysis"]["probabilities"]
    market = match["market_implied"]
    rows = [
        ("主胜", model["home_win"], market["home"]),
        ("平局", model["draw"], market["draw"]),
        ("客胜", model["away_win"], market["away"]),
    ]
    st.markdown("**胜平负概率**（绿条模型 · 蓝条庄家隐含）")
    for name, mv, kv in rows:
        st.progress(min(1.0, mv), text=f"{name}  模型 {pct(mv)}  ·  庄家 {pct(kv)}")


def prob_comparison_figure(match: dict) -> go.Figure:
    model = match["result_analysis"]["probabilities"]
    market = match["market_implied"]
    labels = ["主胜", "平局", "客胜"]
    model_vals = [model["home_win"], model["draw"], model["away_win"]]
    market_vals = [market["home"], market["draw"], market["away"]]
    fig = go.Figure()
    fig.add_bar(name="模型", x=labels, y=model_vals, marker_color="#00c896")
    fig.add_bar(name="庄家隐含", x=labels, y=market_vals, marker_color="#3b82f6", opacity=0.75)
    ymax = max(model_vals + market_vals) * 1.18 or 0.1
    fig.update_layout(
        barmode="group",
        height=320,
        margin=dict(l=12, r=12, t=48, b=12),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
        yaxis=dict(tickformat=".0%", title="概率", range=[0, ymax]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_traces(cliponaxis=False)
    return fig


def scorelines_figure(match: dict) -> go.Figure:
    scores = match["score_analysis"]["top_scorelines"]
    df = pd.DataFrame(scores)
    primary = match["score_analysis"].get("primary_score") or match["recommendation"]["pick_score"]
    colors = ["#00c896" if s == primary else "#64748b" for s in df["score"]]
    fig = go.Figure(go.Bar(
        x=df["score"],
        y=df["prob"],
        marker_color=colors,
        text=[pct(p) for p in df["prob"]],
        textposition="outside",
        cliponaxis=False,
    ))
    ymax = max(df["prob"].tolist()) * 1.35 if len(df) else 0.1
    fig.update_layout(
        height=300,
        margin=dict(l=12, r=12, t=40, b=12),
        yaxis=dict(tickformat=".0%", title="概率", range=[0, ymax]),
        xaxis_title="比分",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def expected_goals_figure(match: dict) -> go.Figure:
    sc = match["score_analysis"]
    home = sc["expected_goals"]["home"]
    away = sc["expected_goals"]["away"]
    names = [
        match["team_analysis"]["home"]["display"],
        match["team_analysis"]["away"]["display"],
    ]
    fig = go.Figure(go.Bar(
        x=names,
        y=[home, away],
        marker_color=["#22c55e", "#60a5fa"],
        text=[f"{home:.2f}", f"{away:.2f}"],
        textposition="outside",
        cliponaxis=False,
    ))
    ymax = max(home, away) * 1.35 or 0.1
    fig.update_layout(
        height=280,
        margin=dict(l=12, r=12, t=36, b=12),
        yaxis=dict(title="预期进球", range=[0, ymax]),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def render_summary_metrics(data: dict) -> None:
    rs = data.get("results_summary")
    if not rs:
        return
    c1, c2, c3 = st.columns(3)
    c1.metric("本批已赛", f"{rs['n']} 场")
    c2.metric("胜负命中", f"{rs['hit_1x2']} / {rs['n']}")
    c3.metric("比分命中", f"{rs['hit_score']} / {rs['n']}")
    if rs.get("note"):
        st.caption(zh_text(rs["note"]))


def render_post_match(match: dict) -> None:
    actual = match.get("actual")
    pm = match.get("post_match")
    if not actual or not pm:
        st.warning("暂无赛果数据。")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("实际赛果", actual["score"], actual.get("outcome_zh", ""))
    c2.metric(
        "模型预测",
        f"{pm['model_pick']} · {pm['model_score']}",
        delta="胜负命中" if pm.get("hit_1x2") else "胜负未中",
        delta_color="normal" if pm.get("hit_1x2") else "inverse",
    )
    c3.metric(
        "庄家方向",
        pm.get("market_pick", "—"),
        delta="胜负命中" if pm.get("market_hit_1x2") else "胜负未中",
        delta_color="normal" if pm.get("market_hit_1x2") else "inverse",
    )
    c4.metric(
        "比分预测",
        "命中" if pm.get("hit_score") else "未中",
        delta=f"预测 {pm['model_score']}",
    )

    if pm.get("hit_1x2") and pm.get("hit_score"):
        st.success("胜负与比分双双命中。")
    elif pm.get("hit_1x2"):
        st.info("胜负方向正确，比分有偏差。")
    elif pm.get("hit_score"):
        st.info("比分猜中，胜负方向有偏差。")
    else:
        st.error("胜负与比分均未命中。")

    insights = zh_insights(pm.get("insights") or [])
    if insights:
        st.markdown("**复盘要点**")
        for line in insights:
            st.markdown(f"- {line}")

    elo = pm.get("elo_after", {})
    if elo.get("home") and elo.get("away"):
        h = match["team_analysis"]["home"]["display"]
        a = match["team_analysis"]["away"]["display"]
        st.caption(f"赛后实力指数：{h} {elo['home']} · {a} {elo['away']}")


def render_overview_table(data: dict, *, upcoming_only: bool = False, played_only: bool = False) -> None:
    rows = []
    for m in data["matches"]:
        if upcoming_only and m.get("actual"):
            continue
        if played_only and not m.get("actual"):
            continue
        rec = m["recommendation"]
        row = {
            "轮次": m.get("stage_label", "小组赛"),
            "开球时间": m["kickoff"],
            "对阵": m["title"],
            "模型推荐": f"{rec['pick_1x2']} · {rec['pick_score']}",
            "庄家倾向": m["market_pick_zh"],
            "与庄家": "一致" if m.get("alignment") == "high" else "分歧",
            "预期进球合计": round(m["score_analysis"]["total_xg"], 2),
        }
        if m.get("actual"):
            pm = m.get("post_match", {})
            row["实际比分"] = m["actual"]["score"]
            row["胜负"] = "中" if pm.get("hit_1x2") else "偏"
            row["比分"] = "中" if pm.get("hit_score") else "偏"
            row.pop("与庄家", None)
        rows.append(row)
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_injuries(match: dict) -> None:
    inj = match.get("injuries")
    if not inj:
        st.info("暂无结构化伤停情报。导出数据时请运行 export_data.py 以同步最新伤病库。")
        return

    if inj.get("requires_search"):
        st.warning("部分球队伤停情报可能过期，赛前建议重新检索确认。")

    net = inj.get("net_impact", 0)
    st.markdown(
        f"**净伤病影响** {net:+.2f}（{inj.get('net_label', '—')}）  \n"
        "数值为主队减客队的伤病特征；负值表示客队相对更完整。"
    )

    left, right = st.columns(2)
    for col, side_key in ((left, "home"), (right, "away")):
        side = inj[side_key]
        with col:
            st.markdown(f"#### {side['display']}")
            st.caption(f"更新于 {side.get('updated_at') or '—'} · {side.get('impact_label', '')}")
            if side.get("impact", 0) != 0:
                st.metric("伤病影响系数", f"{side['impact']:+.2f}")
            st.write(side.get("summary", "暂无摘要"))
            if side.get("rotation"):
                st.warning(f"轮换/用人：{side['rotation']}")
            for p in side.get("players") or []:
                note = f" — {p['note']}" if p.get("note") else ""
                st.markdown(f"- **{p['name']}** · {p['status']} · {p['role']}{note}")
            if not side.get("players"):
                st.caption("无具体球员条目")


def render_match_detail(match: dict) -> None:
    rec = match["recommendation"]
    res = match["result_analysis"]
    sc = match["score_analysis"]
    odds = match["market_odds"]

    render_pick_hero(match)
    st.info(zh_summary(rec.get("summary", "")))

    if match.get("actual"):
        st.subheader("赛后对照")
        render_post_match(match)
        st.divider()

    st.subheader("核心数据")
    c1, c2, c3 = st.columns(3)
    c1.metric("推荐胜平负", rec["pick_1x2"], pct(rec["pick_1x2_prob"]))
    c2.metric("推荐比分", rec["pick_score"], pct(rec.get("pick_score_prob", sc.get("primary_prob", 0))))
    c3.metric(
        "预期进球合计",
        f"{sc['total_xg']:.2f}",
        GOALS_TENDENCY_ZH.get(sc.get("total_goals_tendency", ""), sc.get("total_goals_tendency", "")),
    )

    prob_bars(match)

    use_side_by_side = st.session_state.get("wide_charts", True)
    if use_side_by_side:
        left, right = st.columns(2)
        with left:
            st.plotly_chart(prob_comparison_figure(match), use_container_width=True)
        with right:
            st.plotly_chart(scorelines_figure(match), use_container_width=True)
    else:
        st.plotly_chart(prob_comparison_figure(match), use_container_width=True)
        st.plotly_chart(scorelines_figure(match), use_container_width=True)

    st.plotly_chart(expected_goals_figure(match), use_container_width=True)

    o1, o2, o3 = st.columns(3)
    o1.metric("主胜赔率", odds["home"])
    o2.metric("平局赔率", odds["draw"])
    o3.metric("客胜赔率", odds["away"])

    st.subheader("详细解读")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["胜负依据", "比分依据", "伤停情报", "双方情报", "备战与战意"]
    )

    with tab1:
        st.markdown("**胜平负概率排序**")
        for item in res.get("ranked_outcomes", []):
            st.write(f"- {zh_text(item['outcome'])}：{pct(item['prob'])}")
        st.divider()
        for raw in res.get("reasons", []):
            r = zh_reason(raw)
            fav = r.get("favors_zh", "")
            fav_note = f"（倾向{fav}）" if fav else ""
            st.markdown(f"**{r['factor']}** · 权重{r['weight']}{fav_note}  \n{r['detail']}")

    with tab2:
        ge = sc.get("goal_environment") or {}
        if ge.get("active"):
            st.info(
                f"**本届大球环境（P6）**：已赛 {ge.get('n', '—')} 场，场均 {ge.get('avg_goals', '—')} 球，"
                f"相对历史首轮基准抬升系数 **{ge.get('lift', 1):.2f}**。"
                "单边碾压局优先零封比分，对局型热门场厚尾分布略放宽。"
            )
        alt = sc.get("raw_top_score")
        if alt and alt != sc.get("primary_score"):
            st.caption(f"进球模型原始最高比分 {alt}，经校准后主推 {sc.get('primary_score', rec['pick_score'])}。")
        for raw in sc.get("score_reasons", []):
            r = zh_reason(raw)
            sup = r.get("supports", "")
            st.markdown(f"**{r['factor']}** → 支持比分 {sup}  \n{r['detail']}")
        for line in sc.get("prep_impact_summary", []):
            st.caption(zh_text(line))
        notes = sc.get("calibration_notes") or []
        if notes:
            st.markdown("**比分校准说明**")
            for n in notes:
                st.markdown(f"- {zh_text(n)}")

    with tab3:
        render_injuries(match)

    with tab4:
        for side_key, title in (("home", "主队"), ("away", "客队")):
            t = match["team_analysis"][side_key]
            with st.expander(f"{title}：{t['display']}", expanded=True):
                st.write(f"实力指数 **{t['elo']}**")
                st.write(f"主教练 {t.get('coach', '—')}（{zh_text(t.get('coach_style', ''))}）")
                if t.get("strengths"):
                    st.success("优势：" + "；".join(zh_team_notes(t["strengths"])))
                if t.get("weaknesses"):
                    st.warning("隐患：" + "；".join(zh_team_notes(t["weaknesses"])))
                for note in zh_team_notes(t.get("notes", [])[:8]):
                    st.write(f"- {note}")

    with tab5:
        prep = match.get("prep_text") or "暂无备战周期文字分析。"
        st.markdown(zh_text(prep))


def main() -> None:
    st.set_page_config(
        page_title="世界杯小组赛预测看板",
        page_icon="🏆",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_styles()
    data = load_data()
    highlight = match_groups(data)

    labels = [match_label(m) for m in data["matches"]]
    by_label = {match_label(m): m for m in data["matches"]}

    with st.sidebar:
        st.header("🏆 导航")
        view = st.radio(
            "视图",
            ["赛程总览", "积分榜出线", "单场详解", "赛后复盘"],
            label_visibility="collapsed",
        )
        selected = st.selectbox("选择比赛", labels, format_func=lambda x: f"{x} · {by_label[x]['title']}")
        st.session_state["wide_charts"] = st.toggle("宽屏并排图表", value=True)
        st.divider()
        st.caption("本看板仅供研究参考，不构成任何投注建议。")

    render_home_hero(data)

    if view == "赛程总览":
        render_standings_dashboard(highlight_groups=highlight)
        st.divider()
        render_summary_metrics(data)
        st.subheader("6/19 第二轮 · A/B 组（赛前预测）")
        render_overview_table(data, upcoming_only=True)
        st.divider()
        st.subheader("6/18 K/L 组 · 赛后复盘")
        render_overview_table(data, played_only=True)
        st.divider()
        st.subheader("展开查看单场完整解读")
        for m in data["matches"]:
            with st.expander(f"{m['kickoff']} · {m['title']}", expanded=(match_label(m) == selected)):
                render_match_detail(m)

    elif view == "积分榜出线":
        render_standings_dashboard(highlight_groups=highlight, show_all=True)

    elif view == "赛后复盘":
        render_summary_metrics(data)
        st.divider()
        played = [m for m in data["matches"] if m.get("actual")]
        if not played:
            st.warning("本批比赛尚无赛果。")
        for m in played:
            with st.expander(
                f"{m['kickoff']} · {m['title']} · 实际 {m['actual']['score']}",
                expanded=(match_label(m) == selected),
            ):
                render_post_match(m)
                st.divider()
                render_match_detail(m)

    else:
        m = by_label[selected]
        st.header(m["title"])
        render_match_detail(m)


if __name__ == "__main__":
    main()
