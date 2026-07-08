"""本地 Web 应用（给 2-3 人用）。

    python -m kol_analyze.web         # 浏览器打开 http://127.0.0.1:8000

流程：选产品(RM/RC/RO) → 上传后台 xlsx + 大盘截图 → 审阅并修正命名(存记忆库)
     → 补充缺失 → 生成复盘 docx 并下载。每次生成都归档进「历史复盘」。

生成分析用 Claude Code 订阅（CLI），无需官方 API key。
记忆库与历史按产品分开存。
"""

from __future__ import annotations

import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

from flask import (Flask, jsonify, redirect, request, send_file, session)

from . import (analyzer, docx_writer, engine, loader, market, memory,
               metrics, scripts, store, vision)
from .config import PRODUCTS, Settings
from .web_ui import LOGIN_PAGE, PAGE

app = Flask(__name__)
# 部署到线上时用固定密钥（环境变量），本地随机即可
app.secret_key = os.environ.get("KOL_SECRET") or ("kol-local-" + uuid.uuid4().hex)
app.json.sort_keys = False  # 保持产品插入顺序（RM/RC/RO），别按字母排

# 访问密码：设了 KOL_PASSWORD 就要求登录（线上必设，防止链接被外人打开）
ACCESS_PW = os.environ.get("KOL_PASSWORD", "")


@app.before_request
def _guard():
    if not ACCESS_PW:
        return None
    if request.path in ("/login", "/favicon.ico"):
        return None
    if session.get("authed"):
        return None
    if request.path.startswith("/api/"):
        return jsonify({"ok": False, "error": "未登录"}), 401
    return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("pw") == ACCESS_PW:
            session["authed"] = True
            return redirect("/")
        return LOGIN_PAGE.replace("<!--ERR-->", "密码不对，再试一次。")
    return LOGIN_PAGE.replace("<!--ERR-->", "")

SESSIONS: dict[str, dict] = {}
SETTINGS = Settings()
DEFAULT_PRODUCT = next(iter(PRODUCTS))


def _sid() -> str:
    if "sid" not in session:
        session["sid"] = uuid.uuid4().hex
    sid = session["sid"]
    if sid not in SESSIONS:
        SESSIONS[sid] = {"sid": sid, "product": DEFAULT_PRODUCT,
                         "market": market.MarketContext(),
                         "gen": {"status": "idle"}, "meta": {}}
    return sid


def _S() -> dict:
    return SESSIONS[_sid()]


def _wd(st: dict) -> Path:
    return store.session_dir(st["product"], st["sid"])


# --------------------------------------------------------------------------
# 核心：跑分析（不含 Claude 写作，秒级）
# --------------------------------------------------------------------------

def _recompute(st: dict) -> dict:
    mem = memory.load(store.memory_path(st["product"]))
    data_dir = _wd(st) / "data"
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
    a, sa, mem = st["analysis"], st["sa"], st["mem"]
    rows = []
    for l in a.langs:
        for c in l.creatives:
            rows.append({
                "ad_name": c.ad_name, "play": c.play or "", "lang": l.name,
                "influencer": c.influencer or "",
                "scripts": scripts.script_themes(c, mem),
                "formats": scripts.format_tags(c, mem), "tier": c.tier,
                "spend": round(c.spend, 1), "roi7": round((c.roi7 or 0) * 100, 1),
            })
    rows.sort(key=lambda r: r["spend"], reverse=True)
    gaps = [{"name": g.name, "ad": g.ad_market_share, "kol": g.kol_spend_share,
             "pub": g.publish_share, "breakout": g.breakout_rate,
             "verdict": g.verdict, "line": g.one_line} for g in a.gaps]
    migrations = [{"theme": r.theme, "best": r.best_lang, "to": r.migrate_to,
                   "reason": r.reason} for r in sa.migrations[:12]]
    return {
        "product": st["product"], "product_name": PRODUCTS.get(st["product"], st["product"]),
        "detected_products": st["ds"].products,
        "stats": {"creatives": sum(l.count for l in a.langs),
                  "langs": len(a.langs), "scripts": len(sa.scripts),
                  "migrations": len(sa.migrations),
                  "kol_share": st["market"].kol_share_of_total},
        "langs": [{"name": l.name, "count": l.count,
                   "spend_share": round(l.spend_share, 1),
                   "breakout": round(l.breakout_rate, 1) if l.breakout_rate is not None else None}
                  for l in a.langs],
        "rows": rows, "gaps": gaps, "migrations": migrations,
        "memory": memory.to_dict(mem), "missing": _missing(st),
        "notes": st["market"].notes, "history": _history_list(st["product"]),
    }


def _missing(st: dict) -> dict:
    mkt = st["market"]
    inc = [l.name for l in st["analysis"].langs if l.lang in st.get("incomplete", set())]
    return {"market": mkt.is_empty(), "incomplete_langs": sorted(inc),
            "coverage_gaps": st["analysis"].coverage_gaps}


def _history_list(product: str) -> list[dict]:
    return [{"id": e.id, "period": e.period, "title": e.title,
             "created": e.created, "stats": e.stats}
            for e in store.list_history(product)]


# --------------------------------------------------------------------------
# 路由
# --------------------------------------------------------------------------

@app.get("/")
def index():
    _sid()
    return PAGE


@app.get("/api/engine")
def api_engine():
    return jsonify({"engine": engine.available(), "label": engine.label(),
                    "products": PRODUCTS})


@app.post("/api/analyze")
def api_analyze():
    st = _S()
    st["product"] = request.form.get("product") or DEFAULT_PRODUCT
    st["meta"] = {"title": request.form.get("title") or "月度 KOL 广告复盘",
                  "period": request.form.get("period") or ""}
    wd = _wd(st)
    for f in request.files.getlist("data"):
        if f.filename:
            f.save(wd / "data" / Path(f.filename).name)
    shots = []
    for f in request.files.getlist("shots"):
        if f.filename:
            p = wd / "shots" / Path(f.filename).name
            f.save(p)
            shots.append(str(p))
    if shots:
        st["market"] = vision.read_screenshots(shots, SETTINGS)
    return jsonify(_recompute(st))


@app.post("/api/supplement")
def api_supplement():
    st = _S()
    wd = _wd(st)
    for f in request.files.getlist("data"):
        if f.filename:
            f.save(wd / "data" / Path(f.filename).name)
    shots = []
    for f in request.files.getlist("shots"):
        if f.filename:
            p = wd / "shots" / Path(f.filename).name
            f.save(p)
            shots.append(str(p))
    if shots:
        newmkt = vision.read_screenshots(shots, SETTINGS)
        if not newmkt.is_empty():
            st["market"] = newmkt
    return jsonify(_recompute(st))


@app.post("/api/market")
def api_market():
    st = _S()
    st["market"] = market.from_dict(request.get_json(force=True))
    return jsonify(_recompute(st))


@app.post("/api/correct")
def api_correct():
    st = _S()
    body = request.get_json(force=True)
    mem = memory.load(store.memory_path(st["product"]))
    scope = body.get("scope", "keyword")
    common = dict(add_script=body.get("add_script", []),
                  set_script=body.get("set_script", []),
                  add_format=body.get("add_format", []), note=body.get("note", ""))
    if scope == "exact":
        mem.add_play_override(body.get("key", ""), **common)
    elif scope == "keyword":
        mem.keyword_rules.append(memory.KeywordRule(match=body.get("match", ""), **common))
    elif scope == "influencer":
        mem.influencer_alias[body.get("from", "")] = body.get("to", "")
    elif scope == "lang":
        mem.lang_overrides[body.get("key", "")] = body.get("to", "")
    mem.save(store.memory_path(st["product"]))
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
            out = _wd(state) / "复盘.docx"
            docx_writer.render(data, state["analysis"], state["sa"], out)
            created = datetime.now(timezone.utc).astimezone().strftime("%Y%m%d-%H%M")
            stats = {"creatives": sum(l.count for l in state["analysis"].langs),
                     "langs": len(state["analysis"].langs),
                     "migrations": len(state["sa"].migrations)}
            entry = store.archive(state["product"], state["meta"]["period"] or "复盘",
                                  state["meta"]["title"], created, out, data, stats)
            state["gen"] = {"status": "done", "file": str(out), "hid": entry.id}
        except Exception as e:  # noqa
            state["gen"] = {"status": "error", "error": str(e)}

    threading.Thread(target=worker, args=(st,), daemon=True).start()
    return jsonify({"ok": True, "status": "running", "engine": engine.label()})


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


@app.get("/api/history")
def api_history():
    prod = request.args.get("product") or _S()["product"]
    return jsonify({"product": prod, "history": _history_list(prod)})


@app.get("/api/history/download")
def api_history_download():
    prod = request.args.get("product") or _S()["product"]
    entry = store.get_history(prod, request.args.get("id", ""))
    if not entry or not entry.report().exists():
        return jsonify({"ok": False, "error": "历史记录不存在。"}), 404
    return send_file(entry.report(), as_attachment=True,
                     download_name=f"{entry.title}_{entry.period}.docx")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    args = ap.parse_args()
    print(f"KOL 复盘分析 · 本地 Web —— 引擎：{engine.label()}")
    print(f"产品：{'、'.join(f'{k}({v})' for k, v in PRODUCTS.items())}")
    print(f"打开浏览器： http://{args.host}:{args.port}")
    app.run(host=args.host, port=args.port, threaded=True)


if __name__ == "__main__":
    main()
