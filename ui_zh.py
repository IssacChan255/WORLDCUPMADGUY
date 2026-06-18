"""将模型/数据中的英文术语转为中文读者可读的表述。"""
from __future__ import annotations

import re
from typing import Any, Optional

FAVORS_ZH = {
    "home": "主队",
    "away": "客队",
    "draw": "平局",
    "even": "双方均势",
}

WEIGHT_ZH = {
    "高": "高",
    "中": "中",
    "低": "低",
    "参考": "参考",
    "风险提示": "风险提示",
}

ALIGNMENT_ZH = {
    "high": "模型与庄家方向一致",
    "split": "模型与庄家存在分歧",
}

DRAW_RULE_ZH = {
    "p1_competitive_draw": "势均力敌平局信号",
    "p2_away_favorite_stalemate": "客队强势僵持",
    "p2_bunker_underdog": "守平型弱队僵持",
    "p2_extreme_favorite_caution": "极端热门防冷平",
    "p3_moderate_favorite_stalemate": "中等热门僵持",
    "p3_bunker_away_stalemate": "主队小热门对守平客队",
}

GOALS_TENDENCY_ZH = {
    "偏大球": "偏大球",
    "偏小球": "偏小球",
    "中等进球": "进球数中等",
}

TEAM_SLUG_ZH = {
    "portugal": "葡萄牙",
    "congo": "刚果(金)",
    "england": "英格兰",
    "croatia": "克罗地亚",
    "ghana": "加纳",
    "panama": "巴拿马",
    "uzbekistan": "乌兹别克斯坦",
    "colombia": "哥伦比亚",
}


def zh_text(text: str) -> str:
    """把常见英文碎片替换为中文说明。"""
    if not text:
        return text
    s = str(text)
    repl = [
        (r"\bPoisson\b", "进球模型"),
        (r"泊松矩阵", "进球概率矩阵"),
        (r"\bxG\b", "预期进球"),
        (r"xG合计", "预期进球合计"),
        (r"\bElo\b", "实力指数"),
        (r"Elo 纸面", "纸面实力"),
        (r"Elo 差", "实力指数差"),
        (r"\bλ\b", "进球期望"),
        (r"本场 λ", "本场进球期望"),
        (r"\bv4\b", "机器学习模型"),
        (r"\bMD1\b", "小组赛首轮"),
        (r"\bBUNKER\b", "守平型弱队"),
        (r"\bCOLLAPSE\b", "易崩盘弱队"),
        (r"\bSTAR_OPENER\b", "巨星队揭幕战"),
        (r"\bhigh_press\b", "高位逼抢"),
        (r"\bargmax\b", "概率最高项"),
        (r"\bTop\s*5\b", "前五"),
        (r"\bTop\s*3\b", "前三"),
        (r"\b1X2\b", "胜平负"),
        (r"\bP0\b", "平局校准"),
        (r"\bP1\b", "平局推荐"),
        (r"\bP2\b", "大热门校准"),
        (r"\bP3\b", "中等热门校准"),
        (r"\bP4\b", "比分对齐"),
        (r"\bP5\b", "大比分尾部"),
        (r"\bP6\b", "大球环境"),
        (r"\bNB\b", "厚尾分布"),
        (r"主推", "推荐"),
        (r"纸面", "纸面"),
        (r"injury_impact", "伤病影响"),
        (r"\bUEFA\b", "欧足联"),
        (r"\bCAF\b", "非洲足联"),
        (r"\bAFC\b", "亚足联"),
        (r"\bCONMEBOL\b", "南美足联"),
        (r"\bCONCACAF\b", "中北美足联"),
        (r"\bhome\b", "主队"),
        (r"\baway\b", "客队"),
        (r"\bdraw\b", "平局"),
    ]
    for pat, rep in repl:
        s = re.sub(pat, rep, s, flags=re.IGNORECASE)
    for slug, zh in TEAM_SLUG_ZH.items():
        s = re.sub(rf"\b{re.escape(slug)}\b", zh, s, flags=re.IGNORECASE)
    return s


def zh_model_label(raw: str) -> str:
    mapping = {
        "v4.9.0-v4-p5-score-tails": "机器学习模型 4.9（含大比分尾部校准）",
        "4.10.0-v4-p6-goal-environment": "机器学习模型 4.10（含大球环境校准）",
        "4.9.0-v4-p5-score-tails": "机器学习模型 4.9（含大比分尾部校准）",
        "机器学习模型 4.9 + 泊松进球模型": "机器学习模型 4.9（含大比分尾部校准）",
    }
    if raw in mapping:
        return mapping[raw]
    s = raw or ""
    s = s.replace("Poisson goal_model", "泊松进球模型")
    s = s.replace("goal_model", "进球模型")
    return zh_text(s)


def zh_summary(summary: str) -> str:
    s = zh_text(summary)
    s = s.replace("主推", "推荐结果")
    return s


def zh_reason(reason: dict) -> dict:
    out = dict(reason)
    out["factor"] = zh_text(out.get("factor", ""))
    out["detail"] = zh_text(out.get("detail", ""))
    w = out.get("weight", "")
    out["weight"] = WEIGHT_ZH.get(w, w)
    fav = out.get("favors")
    if fav in FAVORS_ZH:
        out["favors_zh"] = FAVORS_ZH[fav]
    if "supports" in out:
        out["supports"] = zh_text(str(out["supports"]))
    return out


def zh_team_notes(notes: list) -> list[str]:
    return [zh_text(n) for n in notes]


def zh_insights(lines: list) -> list[str]:
    return [zh_text(x) for x in lines]


INJURY_STATUS_ZH = {
    "out": "缺阵",
    "doubtful": "出战存疑",
    "suspended": "停赛",
    "fit": "可出战",
    "returning": "伤愈复出",
}

INJURY_ROLE_ZH = {
    "key": "核心球员",
    "attack": "进攻球员",
    "defense": "防守球员",
    "rotation": "轮换球员",
}

NOTE_ZH = {
    "Achilles": "跟腱伤",
    "achilles": "跟腱伤",
}


def zh_injury_note(note: str) -> str:
    s = zh_text(note or "")
    for en, zh in NOTE_ZH.items():
        s = s.replace(en, zh)
    return s


def _impact_label(net: float) -> str:
    if net > 0.08:
        return "主队阵容更完整"
    if net < -0.08:
        return "客队阵容更完整"
    return "双方伤病影响接近"


def zh_injury_side(side: dict, display: str) -> dict:
    players = []
    for p in side.get("players") or []:
        status = (p.get("status") or "fit").lower()
        role = (p.get("role") or "rotation").lower()
        players.append({
            "name": p.get("name", "—"),
            "status": INJURY_STATUS_ZH.get(status, status),
            "role": INJURY_ROLE_ZH.get(role, role),
            "note": zh_injury_note(p.get("note", "")),
        })
    impact = float(side.get("injury_impact", 0))
    return {
        "display": display,
        "summary": zh_text(side.get("summary", "暂无情报")),
        "impact": impact,
        "impact_label": "阵容受损" if impact < -0.05 else ("阵容齐整" if impact >= 0 else "轻微影响"),
        "rotation": zh_text(side.get("rotation_rumor") or ""),
        "updated_at": side.get("updated_at", ""),
        "players": players,
    }


def zh_injury_bundle(bundle: dict, home_display: str, away_display: str) -> dict:
    if not bundle:
        return {}
    net = float(bundle.get("net_injury_feature", 0))
    home = zh_injury_side(bundle.get("home") or {}, home_display)
    away = zh_injury_side(bundle.get("away") or {}, away_display)
    return {
        "net_impact": net,
        "net_label": _impact_label(net),
        "requires_search": bool(bundle.get("requires_search")),
        "home": home,
        "away": away,
    }
