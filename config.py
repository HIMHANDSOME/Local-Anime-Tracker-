#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""番剧年表配置"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data", "bangumi")
RAW_DIR = os.path.join(DATA_DIR, "raw")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

BANGUMI_API_BASE = "https://api.bgm.tv"
BANGUMI_HEADERS = {
    "User-Agent": "AnimeChronology/1.0 (Anime Timetable Project)",
    "Content-Type": "application/json",
}
REQUEST_DELAY = 1.5
MAX_RETRIES = 3
RETRY_BACKOFF = 5
BATCH_SAVE_INTERVAL = 50
PAGE_SIZE = 50

ANIME_TYPE = 2
CATEGORIES = {0: "其他", 1: "TV", 2: "OVA", 3: "Movie", 5: "WEB"}

SEASONS = {
    "一月": {"en": "winter", "months": [1, 2, 3], "label": "1月-3月"},
    "四月": {"en": "spring", "months": [4, 5, 6], "label": "4月-6月"},
    "七月": {"en": "summer", "months": [7, 8, 9], "label": "7月-9月"},
    "十月": {"en": "fall", "months": [10, 11, 12], "label": "10月-12月"},
}

SEASON_ORDER = ["一月", "四月", "七月", "十月"]
SEASON_COLORS = {
    "一月": "D6E4F0",
    "四月": "E2EFDA",
    "七月": "FFF2CC",
    "十月": "FCE4D6",
}
SEASON_HEADER_COLORS = {
    "一月": "4472C4",
    "四月": "548235",
    "七月": "BF8F00",
    "十月": "C55A11",
}

YEAR_RANGE = (1975, 2026)

WEEKDAY_MAP = {
    "日": 7, "日曜": 7, "星期日": 7, "日曜日": 7,
    "月": 1, "月曜": 1, "星期一": 1, "月曜日": 1,
    "火": 2, "火曜": 2, "星期二": 2, "火曜日": 2,
    "水": 3, "水曜": 3, "星期三": 3, "水曜日": 3,
    "木": 4, "木曜": 4, "星期四": 4, "木曜日": 4,
    "金": 5, "金曜": 5, "星期五": 5, "金曜日": 5,
    "土": 6, "土曜": 6, "星期六": 6, "土曜日": 6,
}
WEEKDAY_CN = {1: "周一", 2: "周二", 3: "周三", 4: "周四", 5: "周五", 6: "周六", 7: "周日"}

FIELD_NAMES = {
    "bangumi_id": "ID",
    "name_jp": "日文名",
    "name_cn": "中文名",
    "year": "年份",
    "season": "季度",
    "air_date": "放送开始",
    "air_weekday": "放送星期",
    "episodes": "集数",
    "category": "类型",
    "studio": "制作公司",
    "score": "评分",
    "watch_status": "观看状态",
}
