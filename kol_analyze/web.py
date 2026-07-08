"""本地 Web 应用（给 2-3 人用）。

    python -m kol_analyze.web         # 然后浏览器打开 http://127.0.0.1:8000

流程：上传后台导出 xlsx + 大盘截图 → 审阅并修正命名（存进记忆库）
     → 补充缺失的国家/截图 → 一键生成复盘 docx 并下载。

生成分析用 Claude Code 订阅（CLI），无需官方 API key。
"""

from __future__ import annotations

import threading
import uuid
from pathlib import Path

from flask import (Flask, jsonify, request, send_file, session)

from . import (analyzer, docx_writer, engine, loader, market, memory,
               metrics, scripts, vision)
from .config import Settings
from .web_ui import PAGE

app = Flask(__name__)
app.secret_key = "kol-local-" + uuid.uuid4().hex

# 工作区：每个会话一个目录放上传文件；记忆库全局共享持久化
# 用绝对路径，避免 send_file 相对 Flask root_path 解析出错
ROOT = Path("kol_workspace").resolve()
ROOT.mkdir(exist_ok=True)
MEMORY_PATH = ROOT / "memory.json"

SESSIONS: dict[str, dict] = {}
SETTINGS = Settings()


def _sid() -> str:
    if "sid" not in session:
        session["sid"] = uuid.uuid4().hex
    sid = session["sid"]
    if sid not in SESSIONS:
        wd = ROOT / sid
        (wd / "data").mkdir(parents=True, exist_ok=True)
        (wd / "shots").mkdir(parents=True, exist_ok=True)
        SESSIONS[sid] = {"wd": wd, "market": market.MarketContext(),
                         "gen": {"status": "idle"}, "meta": {}}
    return sid


def _S() -> dict:
    return SESSIONS[_sid()]


# --------------------------------------------------------------------------
# 核心：跑分析（不含 Claude 写作，秒级）
# --------------------------------------------------------------------------

def _recompute(st: dict) -> dict:
    mem = memory.load(MEMORY_PATH)
    data_dir = st["wd"] / "data"
    files = [f for f in data_dir.iterdir()
             if f.suffix.lower() in (".xlsx", ".xls", ".csv")]
    if not files:
        return {"ok": False, "error": "还没有上传数据文件。"}

    ds = loader.load(data_dir, mem)
    mkt = st["market"]
    if ds.kol_total_spend and not mkt.kol_total_spend:
        mkt.kol_total_spend = ds.kol_total_spend

    analysis = metrics.compute(ds, mkt, SETTINGS.thresholds)
    top = max((l.spend_share for l in analysis.langs), default=0.0)
    incomplete = ({l.lang for l in analysis.langs if l.spend_share < 5.0}
                  if top >= 85.0 else set())
    sa = scripts.analyze(analysis.langs, SETTINGS.thresholds, incomplete, mem)

    st.update(ds=ds, mem=mem, analysis=analysis, sa=sa, incomplete=incomplete)
    return {"ok": True, **_snapshot(st)}


def _snapshot(st: dict) -> dict:
    a = st["analysis"]
    sa = st["sa"]
    mem = st["mem"]

    rows = []
    for l in a.langs:
        for c in l.creatives:
            rows.append({
                "ad_name": c.ad_name,
                "play": c.play or "",
                "lang": l.name,
                "influencer": c.influencer or "",
                "scripts": scripts.script_themes(c, mem),
                "formats": scripts.format_tags(c, mem),
                "tier": c.tier,
                "spend": round(c.spend, 1),
                "roi7": round((c.roi7 or 0) * 100, 1),
            })
    rows.sort(key=lambda r: r["spend"], reverse=True)

    gaps = [{"name": g.name, "ad": g.ad_market_share, "kol": g.kol_spend_share,
             "pub": g.publish_share, "breakout": g.breakout_rate,
             "verdict": g.verdict, "line": g.one_line} for g in a.gaps]

    migrations = [{"theme": r.theme, "best": r.best_lang,
                   "to": r.migrate_to, "reason": r.reason}
                  for r in sa.migrations[:12]]

    missing = _missing(st)
    return {
        "stats": {"creatives": sum(l.count for l in a.langs),
                  "langs": len(a.langs), "scripts": len(sa.scripts),
                  "migrations": len(sa.migrations),
                  "kol_share": st["market"].kol_share_of_total},
        "langs": [{"name": l.name, "count": l.count,
                   "spend_share": round(l.spend_share, 1),
                   "breakout": round(l.breakout_rate, 1) if l.breakout_rate is not None else None}
                  for l in a.langs],
        "rows": rows,
        "gaps": gaps,
        "migrations": migrations,
        "memory": memory.to_dict(mem),
        "missing": missing,
        "notes": st["market"].notes,
    }


def _missing(st: dict) -> dict:
    """检测需要补充的地方：大盘缺失、语言消耗疑似未填充。"""
    mkt = st["market"]
    out = {"market": mkt.is_empty(),
           "incomplete_langs": sorted(
               st["analysis"].langs and
               [l.name for l in st["analysis"].langs if l.lang in st.get("incomplete", set())]
               or [])}
    # 大盘有量但 KOL 完全没产出的语言（覆盖缺口）
    out["coverage_gaps"] = st["analysis"].coverage_gaps
    return out


# --------------------------------------------------------------------------
# 路由
# --------------------------------------------------------------------------

@app.get("/")
def index():
    _sid()
    return PAGE


@app.post("/api/analyze")
def api_analyze():
    st = _S()
    st["meta"] = {"title": request.form.get("title") or "月度 KOL 广告复盘",
                  "period": request.form.get("period") or ""}
    for f in request.files.getlist("data"):
        if f.filename:
            f.save(st["wd"] / "data" / Path(f.filename).name)
    shots = []
    for f in request.files.getlist("shots"):
        if f.filename:
            p = st["wd"] / "shots" / Path(f.filename).name
            f.save(p)
            shots.append(str(p))
    if shots:
        st["market"] = vision.read_screenshots(shots, SETTINGS)
    return jsonify(_recompute(st))


@app.post("/api/supplement")
def api_supplement():
    """补充缺失的国家 excel 或大盘截图，然后重算。"""
    st = _S()
    for f in request.files.getlist("data"):
        if f.filename:
            f.save(st["wd"] / "data" / Path(f.filename).name)
    shots = []
    for f in request.files.getlist("shots"):
        if f.filename:
            p = st["wd"] / "shots" / Path(f.filename).name
            f.save(p)
            shots.append(str(p))
    if shots:
        newmkt = vision.read_screenshots(shots, SETTINGS)
        if not newmkt.is_empty():
            st["market"] = newmkt
    return jsonify(_recompute(st))


@app.post("/api/market")
def api_market():
    """手填/修正大盘数据（截图读不到时）。"""
    st = _S()
    st["market"] = market.from_dict(request.get_json(force=True))
    return jsonify(_recompute(st))


@app.post("/api/correct")
def api_correct():
    """保存一条命名修正到记忆库，并即时重算分类。"""
    st = _S()
    body = request.get_json(force=True)
    mem = memory.load(MEMORY_PATH)
    scope = body.get("scope", "keyword")
    add_script = body.get("add_script", [])
    set_script = body.get("set_script", [])
    add_format = body.get("add_format", [])
    note = body.get("note", "")

    if scope == "exact":
        key = body.get("key", "")
        mem.add_play_override(key, set_script=set_script, add_script=add_script,
                              add_format=add_format, note=note)
    elif scope == "keyword":
        mem.keyword_rules.append(memory.KeywordRule(
            match=body.get("match", ""), add_script=add_script,
            set_script=set_script, add_format=add_format, note=note))
    elif scope == "influencer":
        mem.influencer_alias[body.get("from", "")] = body.get("to", "")
    elif scope == "lang":
        mem.lang_overrides[body.get("key", "")] = body.get("to", "")
    mem.save(MEMORY_PATH)
    return jsonify(_recompute(st))


@app.post("/api/generate")
def api_generate():
    st = _S()
    if "analysis" not in st:
        return jsonify({"ok": False, "error": "请先上传并分析数据。"})
    if st["gen"]["status"] == "running":
        return jsonify({"ok": True, "status": "running"})
    st["gen"] = {"status": "running", "engine": engine.label()}

    def worker(state):
        try:
            data = analyzer.analyze(state["analysis"], state["sa"], SETTINGS,
                                    state["meta"]["title"], state["meta"]["period"])
            out = state["wd"] / "复盘.docx"
            docx_writer.render(data, state["analysis"], state["sa"], out)
            state["gen"] = {"status": "done", "file": str(out)}
        except Exception as e:  # noqa
            state["gen"] = {"status": "error", "error": str(e)}

    threading.Thread(target=worker, args=(st,), daemon=True).start()
    return jsonify({"ok": True, "status": "running", "engine": engine.label()})


@app.get("/api/engine")
def api_engine():
    return jsonify({"engine": engine.available(), "label": engine.label()})


@app.get("/api/status")
def api_status():
    return jsonify(_S()["gen"])


@app.get("/api/download")
def api_download():
    st = _S()
    g = st["gen"]
    if g.get("status") != "done":
        return jsonify({"ok": False, "error": "还没生成完成。"}), 400
    title = st["meta"].get("title", "复盘")
    period = st["meta"].get("period", "")
    return send_file(g["file"], as_attachment=True,
                     download_name=f"{title}_{period or '复盘'}.docx")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    print(f"KOL 复盘分析 · 本地 Web —— 引擎：{engine.label()}")
    print(f"打开浏览器： http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, threaded=True)


if __name__ == "__main__":
    main()
