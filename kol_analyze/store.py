"""按产品分区的工作区 + 历史复盘归档。

    kol_workspace/
      RM/                         # 产品：Rythmix
        memory.json               # 该产品的命名修正记忆库
        sessions/<sid>/data,shots # 当前会话上传的文件
        history/
          5月__20260708-1030/     # 一次归档：周期 + 时间戳
            report.docx
            meta.json             # 产品/周期/标题/时间/统计
            analysis.json         # 生成的叙述 JSON（可回看/重渲染）
"""

from __future__ import annotations

import json
import os
import re
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

# 工作区目录：本地默认 ./kol_workspace；云上用环境变量 KOL_WORKSPACE
# 指向挂载的持久盘（如 /data），这样记忆库与历史在重新部署后也不丢。
ROOT = Path(os.environ.get("KOL_WORKSPACE", "kol_workspace")).resolve()
ROOT.mkdir(parents=True, exist_ok=True)


def _safe(s: str) -> str:
    return re.sub(r"[^\w一-鿿.-]+", "_", str(s)).strip("_") or "未命名"


def product_dir(product: str) -> Path:
    d = ROOT / _safe(product)
    (d / "history").mkdir(parents=True, exist_ok=True)
    return d


def memory_path(product: str) -> Path:
    return product_dir(product) / "memory.json"


def session_dir(product: str, sid: str) -> Path:
    d = product_dir(product) / "sessions" / sid
    (d / "data").mkdir(parents=True, exist_ok=True)
    (d / "shots").mkdir(parents=True, exist_ok=True)
    return d


@dataclass
class HistoryEntry:
    id: str
    product: str
    period: str
    title: str
    created: str
    stats: dict
    dir: Path

    def report(self) -> Path:
        return self.dir / "report.docx"


def archive(product: str, period: str, title: str, created: str,
            docx_path: Path, data: dict, stats: dict) -> HistoryEntry:
    """把一次生成结果归档进历史。created 由调用方传入（时间戳字符串）。

    历史 id 只用 ASCII（时间戳+短随机），避免中文周期在 URL 里出编码问题；
    周期照常存进 meta，界面从 meta 读取展示。
    """
    hid = f"{re.sub(r'[^0-9A-Za-z-]', '', created) or 'run'}-{uuid.uuid4().hex[:4]}"
    hdir = product_dir(product) / "history" / hid
    hdir.mkdir(parents=True, exist_ok=True)
    shutil.copy(docx_path, hdir / "report.docx")
    (hdir / "analysis.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    meta = {"id": hid, "product": product, "period": period, "title": title,
            "created": created, "stats": stats}
    (hdir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return HistoryEntry(hid, product, period, title, created, stats, hdir)


def update_entry(product: str, hid: str, docx_path: Path, data: dict) -> None:
    """用修订后的版本覆盖已有历史条目的 docx 与分析 JSON（不新建条目）。"""
    hdir = product_dir(product) / "history" / _safe(hid)
    if not hdir.exists():
        return
    shutil.copy(docx_path, hdir / "report.docx")
    (hdir / "analysis.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def list_history(product: str) -> list[HistoryEntry]:
    hroot = product_dir(product) / "history"
    out: list[HistoryEntry] = []
    for d in hroot.iterdir() if hroot.exists() else []:
        mp = d / "meta.json"
        if mp.exists():
            m = json.loads(mp.read_text(encoding="utf-8"))
            out.append(HistoryEntry(
                m.get("id", d.name), m.get("product", product),
                m.get("period", ""), m.get("title", ""), m.get("created", ""),
                m.get("stats", {}), d))
    out.sort(key=lambda e: e.created, reverse=True)
    return out


# -------------------------- 草稿（可随时回来改） --------------------------

def draft_dir(product: str) -> Path:
    d = product_dir(product) / "drafts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_draft(product: str, created: str, meta: dict, market_dict: dict,
               data: dict | None, src_data_dir: Path) -> str:
    did = f"{re.sub(r'[^0-9A-Za-z-]', '', created) or 'draft'}-{uuid.uuid4().hex[:4]}"
    d = draft_dir(product) / did
    (d / "data").mkdir(parents=True, exist_ok=True)
    if src_data_dir.exists():
        for f in src_data_dir.iterdir():
            if f.is_file():
                shutil.copy(f, d / "data" / f.name)
    (d / "draft.json").write_text(json.dumps({
        "id": did, "product": product, "created": created, "meta": meta,
        "market": market_dict, "data": data}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    return did


def list_drafts(product: str) -> list[dict]:
    root = draft_dir(product)
    out = []
    for d in root.iterdir() if root.exists() else []:
        j = d / "draft.json"
        if j.exists():
            m = json.loads(j.read_text(encoding="utf-8"))
            out.append({"id": m.get("id", d.name), "created": m.get("created", ""),
                        "meta": m.get("meta", {}), "has_data": bool(m.get("data"))})
    out.sort(key=lambda e: e["created"], reverse=True)
    return out


def get_draft(product: str, did: str) -> dict | None:
    d = draft_dir(product) / _safe(did)
    j = d / "draft.json"
    if not j.exists():
        return None
    m = json.loads(j.read_text(encoding="utf-8"))
    m["_data_dir"] = d / "data"
    return m


def delete_draft(product: str, did: str) -> None:
    d = draft_dir(product) / _safe(did)
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)


def get_history(product: str, hid: str) -> HistoryEntry | None:
    d = product_dir(product) / "history" / _safe(hid)
    mp = d / "meta.json"
    if not mp.exists():
        return None
    m = json.loads(mp.read_text(encoding="utf-8"))
    return HistoryEntry(m["id"], m["product"], m["period"], m["title"],
                        m["created"], m.get("stats", {}), d)
