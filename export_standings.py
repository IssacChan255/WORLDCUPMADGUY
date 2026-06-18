#!/usr/bin/env python3
"""从 skill 赛果库导出 standings.json（积分榜 + 出线形势）。"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SKILL_SCRIPTS = Path.home() / ".cursor/skills/worldcup-betting-analyst/scripts"
OUT_PATH = Path(__file__).resolve().parent / "standings.json"

EXPORT_PY = r'''
import json, sys
from pathlib import Path
sys.path.insert(0, ".")
import elo_store, group_standings as gs
from predict import TEAM_DATA, HOST_NATIONS

elo_store.register_team_data(TEAM_DATA, HOST_NATIONS)
store = json.loads(Path("../data/team_elos.json").read_text(encoding="utf-8"))
standings = gs.build_standings(store)

# team_id -> 中文展示名
zh_names = {}
for key, data in TEAM_DATA.items():
    if key.isascii() and key == key.lower().replace(" ", "_") or " " in key and key.isascii():
        tid = key.strip().lower()
        if tid not in zh_names:
            # prefer short ascii id as canonical
            pass
for key, data in TEAM_DATA.items():
    if not key.isascii():
        continue
    tid = key.strip().lower()
    flag = data.get("flag", "")
    # find chinese alias
    cn = None
    for k2, d2 in TEAM_DATA.items():
        if not k2.isascii() and d2.get("group") == data.get("group") and d2.get("flag") == flag:
            cn = k2
            break
    zh_names[tid] = f"{flag}{cn or tid}"

def enrich_team(team_id, row, standings):
    mot = gs.assess_motivation(team_id, standings)
    outlook = gs.qualification_outlook(team_id, standings)
    return {
        **row,
        "team_id": team_id,
        "display": zh_names.get(team_id, f"{row.get('flag','')}{team_id}"),
        "motivation": mot.get("label", ""),
        "motivation_note": mot.get("note", ""),
        "outlook": outlook.get("path", ""),
        "outlook_detail": outlook.get("format_note", ""),
        "in_best8_third": outlook.get("in_best8_third", False),
        "third_rank": outlook.get("third_rank"),
        "zone": "晋级区" if row["rank"] <= 2 else ("争最佳第三" if row["rank"] == 3 else "出局区"),
    }

groups_out = {}
for letter, group in standings["groups"].items():
    teams = []
    for row in group["teams"]:
        teams.append(enrich_team(row["team"], row, standings))
    groups_out[letter] = {
        "leader_pts": group.get("leader_pts", 0),
        "matches_played_max": group.get("matches_played_max", 0),
        "teams": teams,
    }

third = []
for cand in standings.get("third_place_ranking", []):
    tid = cand["team"]
    third.append({
        **cand,
        "display": zh_names.get(tid, tid),
        "in_cutoff": bool(cand.get("in_best8_cutoff")),
    })

out = {
    "generated": store.get("meta", {}).get("last_updated", ""),
    "meta": {
        "results_count": standings["meta"].get("results_count", 0),
        "matchday": standings["meta"].get("matchday", 0),
        "format": "48队 · 12组 · 前二+8个最好第三出线",
    },
    "groups": groups_out,
    "third_place_ranking": third,
}
print(json.dumps(out, ensure_ascii=False, indent=2))
'''


def main() -> None:
    venv_candidates = [
        Path(__file__).resolve().parent.parent / ".venv" / "bin" / "python3",
        SKILL_SCRIPTS.parent / ".venv" / "bin" / "python3",
    ]
    py = next((p for p in venv_candidates if p.exists()), None)
    if not py:
        py = Path(sys.executable)

    proc = subprocess.run(
        [str(py), "-c", EXPORT_PY],
        cwd=SKILL_SCRIPTS,
        check=True,
        capture_output=True,
        text=True,
    )
    OUT_PATH.write_text(proc.stdout, encoding="utf-8")
    print("Updated", OUT_PATH)


if __name__ == "__main__":
    main()
