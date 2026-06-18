"""积分榜与出线形势看板。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import pandas as pd
import streamlit as st

STANDINGS_PATH = Path(__file__).resolve().parent / "standings.json"

ZONE_CLASS = {
    "晋级区": "q",
    "争最佳第三": "t",
    "出局区": "e",
}


@st.cache_data
def load_standings() -> dict:
    if not STANDINGS_PATH.exists():
        return {}
    return json.loads(STANDINGS_PATH.read_text(encoding="utf-8"))


def _row_class(zone: str, rank: int) -> str:
    if rank <= 2:
        return "q"
    if rank == 3:
        return "t"
    return ZONE_CLASS.get(zone, "e")


def render_group_card(letter: str, group: dict) -> None:
    teams = group.get("teams") or []
    played = group.get("matches_played_max", 0)
    rows_html = []
    for t in teams:
        cls = _row_class(t.get("zone", ""), t["rank"])
        rec = f"{t['w']}胜{t['d']}平{t['l']}负 · {t['gf']}-{t['ga']}"
        rows_html.append(
            f'<div class="standings-row {cls}">'
            f'<span class="rk">{t["rank"]}</span>'
            f'<span class="name">{t["display"]}<div class="rec">{rec}</div></span>'
            f'<span class="pts">{t["pts"]}</span>'
            f"</div>"
        )
    st.markdown(
        f"""
<div class="group-card">
  <div class="group-head">
    <span class="group-letter">{letter} 组</span>
    <span class="group-meta">已赛 {played} 轮</span>
  </div>
  {''.join(rows_html)}
</div>
        """,
        unsafe_allow_html=True,
    )


def render_group_outlook(letter: str, group: dict) -> None:
    st.markdown(f"**{letter} 组出线形势**")
    for t in group.get("teams") or []:
        mot = t.get("motivation", "")
        st.markdown(
            f"""
<div class="outlook-card">
  <div class="team">{t['display']} · 第{t['rank']}名 · {t['pts']}分</div>
  <div class="path">{t.get('outlook', '—')}</div>
  <div class="note">战意：{mot} — {t.get('motivation_note', '')}</div>
</div>
            """,
            unsafe_allow_html=True,
        )


def render_third_place_table(standings: dict) -> None:
    rows = standings.get("third_place_ranking") or []
    if not rows:
        st.caption("小组赛尚未产生足够场次，最好第三排名仅供参考。")
        return
    data = []
    for r in rows[:12]:
        data.append({
            "排名": r.get("third_rank", "—"),
            "小组": f"{r.get('group', '')}组",
            "球队": r.get("display", r.get("team", "")),
            "积分": r["pts"],
            "净胜球": f"{r['gd']:+d}",
            "进前八": "是" if r.get("in_cutoff") else "—",
        })
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)


def render_standings_dashboard(
    *,
    highlight_groups: Optional[list[str]] = None,
    show_all: bool = False,
) -> None:
    standings = load_standings()
    if not standings:
        st.warning("暂无积分榜数据。请在本地运行 `python export_standings.py` 生成 standings.json。")
        return

    meta = standings.get("meta") or {}
    st.markdown("### 小组积分榜")
    st.caption(
        f"赛制：{meta.get('format', '—')} · "
        f"已录入 {meta.get('results_count', '—')} 场 · "
        f"第 {meta.get('matchday', '—')} 轮"
    )

    groups = standings.get("groups") or {}
    letters = sorted(groups.keys())
    if highlight_groups:
        primary = [g for g in highlight_groups if g in groups]
        rest = [g for g in letters if g not in primary]
    else:
        primary, rest = letters[:4], letters[4:]

    if primary:
        cols = st.columns(min(len(primary), 4))
        for i, letter in enumerate(primary):
            with cols[i % len(cols)]:
                render_group_card(letter, groups[letter])

    if show_all and rest:
        st.markdown("#### 其余小组")
        cols2 = st.columns(4)
        for i, letter in enumerate(rest):
            with cols2[i % 4]:
                render_group_card(letter, groups[letter])
    elif rest:
        with st.expander(f"查看其余 {len(rest)} 个小组积分榜"):
            cols2 = st.columns(4)
            for i, letter in enumerate(rest):
                with cols2[i % 4]:
                    render_group_card(letter, groups[letter])

    st.divider()
    st.markdown("### 出线形势解读")

    outlook_letters = highlight_groups if highlight_groups else primary[:2]
    if outlook_letters:
        oc = st.columns(len(outlook_letters))
        for i, letter in enumerate(outlook_letters):
            if letter in groups:
                with oc[i]:
                    render_group_outlook(letter, groups[letter])

    st.markdown("### 小组第三排名（争 8 个出线名额）")
    render_third_place_table(standings)
