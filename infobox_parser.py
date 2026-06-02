#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析 Bangumi infobox 字段"""

import re
import logging
from typing import Dict, Any, Optional

from config import WEEKDAY_MAP, WEEKDAY_CN, CATEGORIES

logger = logging.getLogger(__name__)


def parse_infobox(subject: Dict[str, Any]) -> Dict[str, Any]:
    """从 Subject 对象中解析 infobox 信息"""
    result = {
        "air_weekday": "",
        "studio": "",
        "category": "",
        "director": "",
        "origin": "",
        "episodes_detail": "",
        "chinese_name": "",
    }

    infobox = subject.get("infobox") or []
    if isinstance(infobox, str):
        return result

    for item in infobox:
        if not isinstance(item, dict):
            continue
        key = item.get("key", "")
        value = item.get("value", "")

        if key == "放送星期":
            result["air_weekday"] = _parse_weekday(value)
        elif key == "动画制作":
            result["studio"] = _extract_name(value)
        elif key == "制作公司":
            result["studio"] = result["studio"] or _extract_name(value)
        elif key == "导演":
            result["director"] = _extract_name(value)
        elif key == "原作":
            result["origin"] = _extract_name(value)
        elif key == "话数":
            result["episodes_detail"] = _parse_episodes(value)
        elif key == "集数":
            result["episodes_detail"] = result["episodes_detail"] or _parse_episodes(value)
        elif key == "中文名":
            result["chinese_name"] = _extract_name(value)

    if subject.get("eps") and not result["episodes_detail"]:
        result["episodes_detail"] = str(subject["eps"])

    return result


def _parse_weekday(value) -> str:
    if isinstance(value, list):
        texts = [v.get("v", v.get("name", "")) if isinstance(v, dict) else str(v) for v in value]
        value = " ".join(texts)
    value = str(value).strip()

    for cn_name, num in WEEKDAY_MAP.items():
        if cn_name in value:
            return WEEKDAY_CN.get(num, value)

    weekday_num = subject_weekday_value(value)
    if weekday_num:
        return WEEKDAY_CN.get(weekday_num, value)

    return value


def subject_weekday_value(raw: str) -> Optional[int]:
    m = re.search(r"(\d)", raw)
    if m:
        n = int(m.group(1))
        if 1 <= n <= 7:
            return n
    return None


def _extract_name(value) -> str:
    if isinstance(value, list):
        names = []
        for v in value:
            if isinstance(v, dict):
                names.append(v.get("v", v.get("name", "")))
            else:
                names.append(str(v))
        return "、".join(n for n in names if n)
    if isinstance(value, dict):
        return value.get("v", value.get("name", str(value)))
    return str(value).strip()


def _parse_episodes(value) -> str:
    if isinstance(value, list):
        for v in value:
            if isinstance(v, dict):
                return str(v.get("v", v.get("name", "")))
        return str(value[0]) if value else ""
    return str(value).strip()


PLATFORM_MAP = {
    "TV": "TV",
    "OVA": "OVA",
    "OAD": "OVA",
    "剧场版": "Movie",
    "电影": "Movie",
    "WEB": "WEB",
    "漫画": "其他",
    "小说": "其他",
    "游戏": "其他",
    "其他": "其他",
}


def _classify_category(platform: str, episodes_str: str) -> str:
    if isinstance(platform, str):
        p = platform.strip()
        if p in PLATFORM_MAP:
            return PLATFORM_MAP[p]
        for key, val in PLATFORM_MAP.items():
            if key in p:
                return val
    return "TV" if episodes_str and int(episodes_str or 0) > 1 else "其他"


def subject_to_record(subject: Dict[str, Any]) -> Dict[str, Any]:
    """将 Bangumi Subject 转换为年表记录"""
    info = parse_infobox(subject)

    air_date = subject.get("date") or ""
    year, season = _date_to_year_season(air_date)

    platform = subject.get("platform", "")
    category = _classify_category(platform, info.get("episodes_detail", ""))

    name = subject.get("name") or ""
    name_cn = subject.get("name_cn") or ""
    if name_cn.strip() == name.strip():
        name_cn = ""
    if not name_cn:
        name_cn = info.get("chinese_name", "")

    eps = subject.get("eps")
    eps_str = str(eps) if eps and eps > 0 else (info["episodes_detail"] or "")

    rating = subject.get("rating", {})
    score = rating.get("score", 0) if isinstance(rating, dict) else 0

    return {
        "bangumi_id": subject.get("id", 0),
        "name_jp": name,
        "name_cn": name_cn,
        "year": year,
        "season": season,
        "air_date": air_date,
        "air_weekday": info["air_weekday"],
        "episodes": eps_str,
        "category": category,
        "studio": info["studio"],
        "director": info["director"],
        "score": round(score, 1) if score else 0,
        "watch_status": "",
    }


def _date_to_year_season(date_str: str):
    if not date_str or len(date_str) < 4:
        return 0, ""
    try:
        parts = date_str.split("-")
        year = int(parts[0])
        month = int(parts[1]) if len(parts) > 1 else 0
    except (ValueError, IndexError):
        return 0, ""

    if 1 <= month <= 3:
        season = "一月"
    elif 4 <= month <= 6:
        season = "四月"
    elif 7 <= month <= 9:
        season = "七月"
    elif 10 <= month <= 12:
        season = "十月"
    else:
        season = ""

    return year, season
