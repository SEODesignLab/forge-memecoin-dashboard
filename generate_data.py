#!/usr/bin/env python3
"""Build dashboard-data.json from local paper + cohort files. No trades. No RPC required."""
import json
from datetime import datetime, timezone
from pathlib import Path

BOT = Path("/root/trading/memecoin-bot")
OUT = Path("/root/forge-memecoin-dashboard/data/dashboard-data.json")

def load(name, default):
    p = BOT / name
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text())
    except Exception:
        return default

def main():
    paper = load("memecoin-paper-trades.json", [])
    cohort = load("cohort-state.json", {})
    closed = load("memecoin-completed-trades.json", [])
    positions = load("memecoin-positions.json", [])

    skips = [r for r in paper if r.get("decision") == "SKIP"]
    buys = [r for r in paper if r.get("decision") == "PAPER_BUY"]
    settled = [r for r in buys if r.get("settled") and r.get("pnl_pct") is not None]
    wins = [r for r in settled if r["pnl_pct"] > 0]
    reasons = {}
    for r in skips:
        key = (r.get("reason") or "unknown").split("(")[0].strip()
        reasons[key] = reasons.get(key, 0) + 1
    reason_rows = [{"reason": k, "count": v} for k, v in sorted(reasons.items(), key=lambda kv: -kv[1])]

    wallets = []
    for w, rec in (cohort.get("wallets") or {}).items():
        wallets.append({
            "wallet": w,
            "hits": rec.get("hits", 0),
            "symbols": rec.get("symbols") or [],
            "last": rec.get("last", ""),
        })
    wallets.sort(key=lambda x: -x["hits"])

    narrative = load("narrative-paper.json", [])
    monte = load("narrative-montecarlo.json", {"ran": False, "n": 0, "reason": "no file yet"})
    n_settled = [r for r in narrative if r.get("settled") and r.get("pnl_pct") is not None]
    n_wins = [r for r in n_settled if r["pnl_pct"] > 0]
    live_pnl = round(sum(float(r.get("pnl_usdc") or 0) for r in closed), 2)
    live_wins = sum(1 for r in closed if (r.get("pnl_usdc") or 0) > 0)

    data = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "mode": "PAPER — live buys off",
        "summary": {
            "paper_rows": len(paper),
            "paper_skips": len(skips),
            "paper_buys": len(buys),
            "paper_settled": len(settled),
            "paper_wins": len(wins),
            "paper_win_rate": round(len(wins) / len(settled), 3) if settled else None,
            "need_settled": 50,
            "cohort_runs": cohort.get("runs", 0),
            "cohort_wallets": len(wallets),
            "cohort_qualified": sum(1 for w in wallets if w["hits"] >= 3),
            "live_closes": len(closed),
            "live_wins": live_wins,
            "live_pnl_usdc": live_pnl,
            "open_positions": len(positions) if isinstance(positions, list) else 0,
            "narrative_rows": len(narrative),
            "narrative_open": sum(1 for r in narrative if not r.get("settled")),
            "narrative_settled": len(n_settled),
            "narrative_wins": len(n_wins),
            "narrative_win_rate": round(len(n_wins) / len(n_settled), 3) if n_settled else None,
            "narrative_avg_pnl": round(sum(r["pnl_pct"] for r in n_settled) / len(n_settled), 4) if n_settled else None,
        },
        "skip_reasons": reason_rows[:12],
        "paper": list(reversed(paper[-40:])),
        "narrative_paper": list(reversed(narrative[-30:])),
        "narrative_montecarlo": monte,
        "wallets": wallets[:15],
        "mints": list((cohort.get("seen_mints") or {}).values())[-12:],
        "live_closes": list(reversed(closed[-12:])),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1))
    print(f"wrote {OUT} paper={len(paper)} qualified={data['summary']['cohort_qualified']}")

if __name__ == "__main__":
    main()
