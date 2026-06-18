#!/usr/bin/env python3
"""Regenerate matches.json and index.html from worldcup-betting-analyst models."""
import json
import subprocess
import sys
from pathlib import Path

SKILL_SCRIPTS = Path.home() / ".cursor/skills/worldcup-betting-analyst/scripts"
OUT_DIR = Path(__file__).resolve().parent

# home, away, group, kickoff, title, market_odds, stage_label, tournament_stage
MATCHES = [
    # K/L 组 6/18（已赛，保留复盘）
    ("portugal", "congo", "K", "6/18 01:00", "葡萄牙 vs 刚果(金)", {"home": 1.13, "draw": 5.86, "away": 13.50}, "小组赛首轮", 1 / 3),
    ("england", "croatia", "L", "6/18 04:00", "英格兰 vs 克罗地亚", {"home": 1.52, "draw": 3.55, "away": 5.27}, "小组赛首轮", 1 / 3),
    ("ghana", "panama", "L", "6/18 07:00", "加纳 vs 巴拿马", {"home": 2.07, "draw": 3.00, "away": 3.20}, "小组赛首轮", 1 / 3),
    ("uzbekistan", "colombia", "K", "6/18 10:00", "乌兹别克斯坦 vs 哥伦比亚", {"home": 9.65, "draw": 4.85, "away": 1.22}, "小组赛首轮", 1 / 3),
    # A/B 组 6/19 第二轮（待赛）
    ("czechia", "south africa", "A", "6/19 00:00", "捷克 vs 南非", {"home": 1.99, "draw": 3.31, "away": 4.06}, "小组赛第二轮", 2 / 3),
    ("switzerland", "bosnia", "B", "6/19 03:00", "瑞士 vs 波黑", {"home": 1.58, "draw": 3.60, "away": 5.40}, "小组赛第二轮", 2 / 3),
    ("canada", "qatar", "B", "6/19 06:00", "加拿大 vs 卡塔尔", {"home": 1.50, "draw": 4.32, "away": 6.37}, "小组赛第二轮", 2 / 3),
    ("mexico", "south korea", "A", "6/19 09:00", "墨西哥 vs 韩国", {"home": 1.78, "draw": 3.63, "away": 4.66}, "小组赛第二轮", 2 / 3),
]

EXPORT_PY = r'''
import json, sys, importlib.util
from pathlib import Path
sys.path.insert(0, ".")
_ui = Path("''' + str(OUT_DIR) + r'''") / "ui_zh.py"
spec = importlib.util.spec_from_file_location("ui_zh", _ui)
ui_zh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ui_zh)
zh_summary, zh_text = ui_zh.zh_summary, ui_zh.zh_text
zh_reason = ui_zh.zh_reason
zh_injury_bundle = ui_zh.zh_injury_bundle
import match_brief as mb

MATCHES = json.loads(sys.argv[1])
out = {
    "generated": "2026-06-19",
    "model": "机器学习模型 4.10（含大球环境校准）",
    "batch_label": "K/L 组复盘 + A/B 组第二轮预测",
    "matches": [],
}
map_zh = {"home": "主胜", "draw": "平局", "away": "客胜"}
for row in MATCHES:
    home, away, grp, kick, title, market = row[:6]
    stage_label = row[6] if len(row) > 6 else "小组赛"
    tournament_stage = row[7] if len(row) > 7 else None
    brief = mb.build_match_brief(
        home, away,
        stage_label=stage_label,
        tournament_stage=tournament_stage,
    )
    dr = brief["detailed_report"]
    ml = brief.get("ml") or {}
    mh, md, ma = market["home"], market["draw"], market["away"]
    imp = [1/mh, 1/md, 1/ma]
    s = sum(imp)
    mi = {"home": round(imp[0]/s,4), "draw": round(imp[1]/s,4), "away": round(imp[2]/s,4)}
    market_pick = "home" if mi["home"]>=mi["draw"] and mi["home"]>=mi["away"] else ("away" if mi["away"]>=mi["draw"] else "draw")
    rec = dict(dr["recommendation"])
    rec["summary"] = zh_summary(rec.get("summary", ""))
    score = dict(dr["score_analysis"])
    score["score_reasons"] = [zh_reason(r) for r in score.get("score_reasons", [])]
    if ml.get("poisson_head", {}).get("calibration_notes"):
        score["calibration_notes"] = [zh_text(x) for x in ml["poisson_head"]["calibration_notes"]]
    res = dict(dr["result_analysis"])
    res["reasons"] = [zh_reason(r) for r in res.get("reasons", [])]
    ta = dr["team_analysis"]
    injuries = zh_injury_bundle(
        brief.get("injuries") or {},
        ta["home"]["display"],
        ta["away"]["display"],
    )
    out["matches"].append({
        "id": len(out["matches"]) + 1,
        "title": title, "home": home, "away": away,
        "group": grp, "kickoff": kick,
        "stage_label": stage_label,
        "market_odds": market, "market_implied": mi,
        "market_pick_zh": map_zh[market_pick],
        "alignment": "high" if dr["result_analysis"]["pick_key"] == market_pick else "split",
        "draw_pick_applied": ml.get("draw_pick_applied", False),
        "draw_pick_rule": ml.get("draw_pick_rule"),
        "recommendation": rec,
        "result_analysis": res,
        "score_analysis": score,
        "team_analysis": ta,
        "injuries": injuries,
        "prep_text": zh_text(brief.get("prep_cycle", {}).get("text_block", "")),
        "standings_context": brief.get("standings_snapshot"),
        "motivation": brief.get("motivation"),
    })
print(json.dumps(out, ensure_ascii=False, indent=2))
'''


def enrich_post_match(data: dict) -> None:
    """把已赛结果与中文复盘写回 matches.json。"""
    import json as _json
    from pathlib import Path as _Path

    skill = SKILL_SCRIPTS.parent / "data" / "team_elos.json"
    if not skill.exists():
        return
    store = _json.loads(skill.read_text(encoding="utf-8"))
    recent = {(r["home"], r["away"]): r for r in store["results"][-4:]}

    insights = {
        ("portugal", "congo"): [
            "模型高估葡萄牙统治力：刚果实际预期进球更高，维萨补时扳平",
            "平局概率模型给出 22%，赛果为平局但未作为主推",
            "庄家隐含平局仅 15%，本场为最大冷门",
        ],
        ("england", "croatia"): [
            "模型错判客胜，实际英格兰 4-2 大胜，与庄家方向一致",
            "平局概率被压至极低，错把势均力敌判成克罗地亚占优",
            "图赫尔轮换担忧未兑现，凯恩与贝林厄姆主导进攻",
        ],
        ("ghana", "panama"): [
            "推荐主胜且比分 1-0，胜负与比分双双命中",
            "模型与庄家方向一致，本场表现最佳",
        ],
        ("uzbekistan", "colombia"): [
            "客胜方向命中，实际 1-3 对比推荐 0-2 差一球",
            "哥伦比亚定位球与迪亚斯个人能力超出纸面预期",
        ],
    }

    def _label(hg, ag):
        if hg > ag:
            return 2, "主胜"
        if hg < ag:
            return 0, "客胜"
        return 1, "平局"

    hits_1x2 = hits_score = 0
    for m in data["matches"]:
        r = recent.get((m["home"], m["away"]))
        if not r:
            continue
        hg, ag = r["home_goals"], r["away_goals"]
        true_i, true_zh = _label(hg, ag)
        pred_map = {"home": 2, "draw": 1, "away": 0}
        pred_i = pred_map[m["result_analysis"]["pick_key"]]
        pred_score = m["recommendation"]["pick_score"]
        actual_score = f"{hg}-{ag}"
        hit_1x2 = pred_i == true_i
        hit_score = pred_score == actual_score
        hits_1x2 += int(hit_1x2)
        hits_score += int(hit_score)
        m["actual"] = {
            "score": actual_score,
            "outcome_zh": true_zh,
            "home_goals": hg,
            "away_goals": ag,
            "date": r.get("date", "2026-06-17"),
        }
        m["post_match"] = {
            "hit_1x2": hit_1x2,
            "hit_score": hit_score,
            "model_pick": m["recommendation"]["pick_1x2"],
            "model_score": pred_score,
            "market_pick": m["market_pick_zh"],
            "market_hit_1x2": m["market_pick_zh"] == true_zh,
            "insights": insights.get((m["home"], m["away"]), []),
            "elo_after": {
                "home": store["elos"].get(m["home"]),
                "away": store["elos"].get(m["away"]),
            },
        }

    played_n = sum(1 for m in data["matches"] if m.get("actual"))
    if played_n:
        data["results_summary"] = {
            "n": played_n,
            "hit_1x2": hits_1x2,
            "hit_score": hits_score,
            "note": "K/L 组 6/18 四场赛后复盘（A/B 组 6/19 四场为赛前预测）",
        }
    data["md1_total"] = {
        "matches_played": store["meta"]["results_count"],
        "md1_backtest_1x2": "21/24",
        "md1_backtest_score": "10/24",
    }
    data["md2_preview"] = {
        "kickoff": "6/19",
        "groups": ["A", "B"],
        "note": "A 组墨西哥、韩国同 3 分领跑；B 组四队各 1 分，第二轮形势胶着",
    }


def main() -> None:
    venv_candidates = [
        OUT_DIR.parent / ".venv" / "bin" / "python3",
        SKILL_SCRIPTS.parent / ".venv" / "bin" / "python3",
    ]
    venv_python = next((p for p in venv_candidates if p.exists()), None)
    if not venv_python:
        print("Missing venv python. Tried:", *venv_candidates, sep="\n  ", file=sys.stderr)
        sys.exit(1)

    payload = json.dumps(MATCHES, ensure_ascii=False)
    proc = subprocess.run(
        [str(venv_python), "-c", EXPORT_PY, payload],
        cwd=SKILL_SCRIPTS,
        check=True,
        capture_output=True,
        text=True,
    )
    matches_path = OUT_DIR / "matches.json"
    data = json.loads(proc.stdout)
    enrich_post_match(data)
    matches_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    standings_script = OUT_DIR / "export_standings.py"
    if standings_script.exists():
        subprocess.run([str(venv_python), str(standings_script)], check=True, cwd=OUT_DIR)

    html_builder = OUT_DIR / "_build_html.py"
    if html_builder.exists():
        subprocess.run([sys.executable, str(html_builder)], check=True, cwd=OUT_DIR)
        print("Updated", matches_path, "and index.html")
    else:
        print("Updated", matches_path)


if __name__ == "__main__":
    main()
