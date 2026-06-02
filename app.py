#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""番剧年表 Web UI"""

import json
import queue
import threading
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from flask import (
    Flask, render_template, request, jsonify,
    Response, send_from_directory, url_for,
)

from config import DATA_DIR, RAW_DIR, OUTPUT_DIR, SEASONS, SEASON_ORDER
from chronology_store import ChronologyStore
from chronology_exporter import ChronologyExporter
from season_builder import SeasonBuilder
from bangumi_collector import BangumiClient

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

store = ChronologyStore()
anime_data: List[Dict[str, Any]] = []
collect_queue: queue.Queue = queue.Queue()
collect_running = threading.Event()


def load_data():
    global anime_data
    anime_data = store.load_all_from_files()
    # Enrich with _weekday_num for sorting
    from config import WEEKDAY_CN
    wd_rev = {v: k for k, v in WEEKDAY_CN.items()}
    for a in anime_data:
        a["_weekday_num"] = wd_rev.get(a.get("air_weekday", ""), 0)
    logger.info(f"已加载 {len(anime_data)} 条数据")


SORT_FIELDS = {
    "name_jp": ("name_jp", str),
    "name_cn": ("name_cn", str),
    "category": ("category", str),
    "episodes": ("_eps_num", int),
    "air_date": ("air_date", str),
    "air_weekday": ("_weekday_num", int),
    "studio": ("studio", str),
    "score": ("score", float),
    "watch_status": ("watch_status", str),
}

WATCH_STATUS_ORDER = {"想看": 1, "在看": 2, "看过": 3, "搁置": 4, "抛弃": 5}


def _sort_key(field: str):
    """Return a key function for sorting by the given field."""
    if field not in SORT_FIELDS:
        field = "air_date"
    attr, _type = SORT_FIELDS[field]

    def key(a):
        v = a.get(attr)
        if field == "episodes":
            try:
                return int(v) if v else 0
            except (ValueError, TypeError):
                return 0
        if field == "air_weekday":
            return a.get("_weekday_num", 0)
        if field == "score":
            return float(v) if v else 0.0
        if field == "watch_status":
            return WATCH_STATUS_ORDER.get(v, 99)
        return v or ""

    return key


def filter_anime(
    data: List[Dict[str, Any]],
    year: Optional[int] = None,
    season: Optional[str] = None,
    category: Optional[str] = None,
    watch_status: Optional[str] = None,
    q: Optional[str] = None,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = None,
    page: int = 1,
    per_page: int = 50,
):
    filtered = data
    if year:
        filtered = [a for a in filtered if a.get("year") == year]
    if season:
        filtered = [a for a in filtered if a.get("season") == season]
    if category:
        filtered = [a for a in filtered if a.get("category") == category]
    if watch_status:
        filtered = [a for a in filtered if a.get("watch_status") == watch_status]
    if q:
        ql = q.lower()
        filtered = [
            a
            for a in filtered
            if ql in (a.get("name_jp") or "").lower()
            or ql in (a.get("name_cn") or "").lower()
        ]

    # Default sort direction is descending
    if not sort_by:
        sort_by = "air_date"
    sort_dir = sort_dir or "desc"

    reverse = sort_dir == "desc"
    filtered = sorted(filtered, key=_sort_key(sort_by), reverse=reverse)

    total = len(filtered)
    start = (page - 1) * per_page
    return filtered[start : start + per_page], total


def compute_stats():
    if not anime_data:
        return {}
    by_year: Dict[int, int] = {}
    by_season: Dict[str, int] = {}
    by_category: Dict[str, int] = {}
    for a in anime_data:
        y = a.get("year", 0)
        s = a.get("season", "")
        c = a.get("category", "")
        by_year[y] = by_year.get(y, 0) + 1
        by_season[s] = by_season.get(s, 0) + 1
        by_category[c] = by_category.get(c, 0) + 1

    has_cn = sum(1 for a in anime_data if a.get("name_cn"))
    has_date = sum(1 for a in anime_data if a.get("air_date") and len(a.get("air_date", "")) >= 8)
    has_eps = sum(1 for a in anime_data if a.get("episodes"))
    has_studio = sum(1 for a in anime_data if a.get("studio"))

    years_sorted = sorted(by_year.keys())
    year_trend = [{"year": y, "count": by_year[y]} for y in years_sorted]

    season_dist = [{"season": s, "count": by_season.get(s, 0)} for s in SEASON_ORDER]

    cat_sorted = sorted(by_category.items(), key=lambda x: -x[1])
    category_dist = [{"category": k, "count": v} for k, v in cat_sorted]

    return {
        "total": len(anime_data),
        "year_range": f"{min(years_sorted)}-{max(years_sorted)}" if years_sorted else "",
        "year_trend": year_trend,
        "season_dist": season_dist,
        "category_dist": category_dist,
        "coverage": {
            "chinese_title": {"count": has_cn, "pct": round(has_cn / len(anime_data) * 100, 1)},
            "air_date": {"count": has_date, "pct": round(has_date / len(anime_data) * 100, 1)},
            "episodes": {"count": has_eps, "pct": round(has_eps / len(anime_data) * 100, 1)},
            "studio": {"count": has_studio, "pct": round(has_studio / len(anime_data) * 100, 1)},
        },
    }


# ── Pages ──────────────────────────────────────────────────────────────


@app.route("/")
def dashboard():
    stats = compute_stats()
    return render_template("dashboard.html", stats=stats)


@app.route("/browse")
def browse():
    return render_template("browse.html")


@app.route("/collect")
def collect_page():
    return render_template("collect.html")


@app.route("/export")
def export_page():
    files = []
    if os.path.exists(OUTPUT_DIR):
        for f in sorted(os.listdir(OUTPUT_DIR)):
            if f.endswith(".xlsx"):
                fpath = os.path.join(OUTPUT_DIR, f)
                files.append({"name": f, "size": f"{os.path.getsize(fpath) / 1024:.0f} KB"})
    return render_template("export.html", files=files)


# ── API ────────────────────────────────────────────────────────────────


@app.route("/api/stats")
def api_stats():
    return jsonify(compute_stats())


@app.route("/api/anime")
def api_anime():
    year = request.args.get("year", type=int)
    season = request.args.get("season")
    category = request.args.get("category")
    watch_status = request.args.get("watch_status")
    q = request.args.get("q")
    sort_by = request.args.get("sort_by")
    sort_dir = request.args.get("sort_dir")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)

    items, total = filter_anime(
        anime_data, year, season, category, watch_status, q,
        sort_by, sort_dir, page, per_page,
    )

    years = sorted(set(a.get("year", 0) for a in anime_data if a.get("year")))
    categories = sorted(set(a.get("category", "") for a in anime_data if a.get("category")))
    watch_statuses = sorted(set(a.get("watch_status", "") for a in anime_data if a.get("watch_status")))

    return jsonify(
        {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": max(1, (total + per_page - 1) // per_page),
            "filters": {"years": years, "seasons": SEASON_ORDER, "categories": categories, "watch_statuses": watch_statuses},
        }
    )


@app.route("/api/anime/<int:bangumi_id>", methods=["PUT"])
def api_update_anime(bangumi_id):
    data = request.get_json()
    new_status = data.get("watch_status", "")

    for a in anime_data:
        if a.get("bangumi_id") == bangumi_id:
            a["watch_status"] = new_status
            _persist_watch_status(a)
            return jsonify({"ok": True})

    return jsonify({"ok": False, "error": "not found"}), 404


def _persist_watch_status(anime: Dict[str, Any]):
    year = anime.get("year", 0)
    season = anime.get("season", "")
    season_en = SEASONS.get(season, {}).get("en", "")
    if not season_en:
        return

    cache_path = os.path.join(RAW_DIR, f"{year}_{season_en}.json")
    if not os.path.exists(cache_path):
        return

    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            season_data = json.load(f)
        for item in season_data:
            if item.get("bangumi_id") == anime.get("bangumi_id"):
                item["watch_status"] = anime["watch_status"]
                break
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(season_data, f, ensure_ascii=False)
    except Exception as e:
        logger.error(f"持久化观看状态失败: {e}")


@app.route("/api/collect", methods=["POST"])
def api_collect():
    if collect_running.is_set():
        return jsonify({"ok": False, "error": "收集任务正在运行中"}), 409

    params = request.get_json() or {}
    start_year = params.get("start_year", 1975)
    end_year = params.get("end_year", 2026)
    enrich = params.get("enrich", False)
    no_cache = params.get("no_cache", False)

    collect_running.set()

    def run():
        try:
            builder = SeasonBuilder(use_cache=not no_cache)

            def on_progress(completed, total, year, season, count):
                collect_queue.put(
                    {
                        "completed": completed,
                        "total": total,
                        "year": year,
                        "season": season,
                        "count": count,
                    }
                )

            result = builder.collect_all(start_year, end_year, progress_callback=on_progress)

            if enrich:
                builder.enrich_details(result)
                store.save_all(result)

            load_data()
        except Exception as e:
            logger.error(f"收集异常: {e}")
            collect_queue.put({"error": str(e), "completed": -1, "total": -1})
        finally:
            collect_running.clear()

    t = threading.Thread(target=run, daemon=True)
    t.start()
    return jsonify({"ok": True})


@app.route("/api/collect/progress")
def api_collect_progress():
    def generate():
        while True:
            try:
                data = collect_queue.get(timeout=30)
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
                if data.get("completed", 0) >= data.get("total", 1) or data.get("error"):
                    break
            except queue.Empty:
                yield ": keepalive\n\n"

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/collect/status")
def api_collect_status():
    return jsonify({"running": collect_running.is_set()})


@app.route("/api/export", methods=["POST"])
def api_export():
    params = request.get_json() or {}
    filename = params.get("filename", "")
    by_year = params.get("by_year", False)

    exporter = ChronologyExporter()

    if by_year:
        files = exporter.export_by_year(anime_data)
        return jsonify({"ok": True, "files": [os.path.basename(f) for f in files]})

    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"番剧年表_{timestamp}.xlsx"

    filepath = exporter.export(anime_data, filename=filename)
    if filepath:
        return jsonify({"ok": True, "filename": os.path.basename(filepath)})
    return jsonify({"ok": False, "error": "导出失败"}), 500


@app.route("/api/export/download/<path:filename>")
def api_download(filename):
    return send_from_directory(OUTPUT_DIR, filename, as_attachment=True)


@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    load_data()
    return jsonify({"ok": True, "total": len(anime_data)})


# ── Main ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    load_data()
    app.run(host="0.0.0.0", port=5000, debug=True)
