#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""季度化数据存储，支持断点续传"""

import json
import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from config import DATA_DIR, RAW_DIR, SEASONS, SEASON_ORDER

logger = logging.getLogger(__name__)


class ChronologyStore:
    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        self.raw_dir = os.path.join(data_dir, "raw")
        os.makedirs(self.raw_dir, exist_ok=True)

    def season_cache_path(self, year: int, season_en: str) -> str:
        return os.path.join(self.raw_dir, f"{year}_{season_en}.json")

    def has_season_cache(self, year: int, season_en: str) -> bool:
        path = self.season_cache_path(year, season_en)
        if not os.path.exists(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return len(data) > 0
        except Exception:
            return False

    def save_season(self, year: int, season: str, anime_list: List[Dict[str, Any]]):
        season_info = SEASONS.get(season, {})
        season_en = season_info.get("en", "unknown")
        path = self.season_cache_path(year, season_en)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(anime_list, f, ensure_ascii=False, indent=2)
            logger.info(f"已缓存 {year}年{season}: {len(anime_list)} 条 -> {path}")
        except Exception as e:
            logger.error(f"保存季度缓存失败: {e}")

    def load_season(self, year: int, season_en: str) -> List[Dict[str, Any]]:
        path = self.season_cache_path(year, season_en)
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"加载季度缓存失败: {e}")
            return []

    def save_all(self, anime_list: List[Dict[str, Any]]) -> str:
        os.makedirs(self.data_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d")
        path = os.path.join(self.data_dir, f"anime_chronology_{timestamp}.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(anime_list, f, ensure_ascii=False)
            logger.info(f"完整数据已保存: {path} ({len(anime_list)} 条)")
        except Exception as e:
            logger.error(f"保存完整数据失败: {e}")
        return path

    def load_all(self) -> List[Dict[str, Any]]:
        all_anime = []
        if not os.path.exists(self.raw_dir):
            return all_anime

        seen_ids = set()
        for year in sorted(os.listdir(self.raw_dir)):
            # Also scan data_dir for season files
            pass

        for season in SEASON_ORDER:
            season_en = SEASONS[season]["en"]
            for fname in sorted(os.listdir(self.raw_dir)):
                if fname.endswith(f"_{season_en}.json"):
                    try:
                        with open(os.path.join(self.raw_dir, fname), "r", encoding="utf-8") as f:
                            data = json.load(f)
                        for anime in data:
                            bid = anime.get("bangumi_id")
                            if bid and bid not in seen_ids:
                                seen_ids.add(bid)
                                all_anime.append(anime)
                    except Exception:
                        pass

        all_anime.sort(key=lambda x: (x.get("year", 0), SEASON_ORDER.index(x.get("season", "")) if x.get("season") in SEASON_ORDER else 4, x.get("air_date") or ""))
        return all_anime

    def load_all_from_files(self) -> List[Dict[str, Any]]:
        """从所有 raw 缓存文件加载，去重"""
        all_anime = []
        seen_ids = set()

        if not os.path.exists(self.raw_dir):
            return all_anime

        for fname in sorted(os.listdir(self.raw_dir)):
            if not fname.endswith(".json") or fname.startswith("api_"):
                continue
            fpath = os.path.join(self.raw_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    for anime in data:
                        bid = anime.get("bangumi_id")
                        if bid and bid not in seen_ids:
                            seen_ids.add(bid)
                            all_anime.append(anime)
                        elif not bid:
                            all_anime.append(anime)
            except Exception as e:
                logger.warning(f"加载 {fname} 失败: {e}")

        season_idx = {s: i for i, s in enumerate(SEASON_ORDER)}
        all_anime.sort(key=lambda x: (
            x.get("year", 0),
            season_idx.get(x.get("season", ""), 4),
            x.get("air_date") or "",
            x.get("name_jp") or "",
        ))
        return all_anime

    def get_stats(self, anime_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not anime_list:
            return {}

        stats = {"total": len(anime_list), "by_year": {}, "by_season": {}, "by_category": {}}

        for anime in anime_list:
            year = anime.get("year", "未知")
            season = anime.get("season", "未知")
            cat = anime.get("category", "未知")

            stats["by_year"][year] = stats["by_year"].get(year, 0) + 1
            stats["by_season"][season] = stats["by_season"].get(season, 0) + 1
            stats["by_category"][cat] = stats["by_category"].get(cat, 0) + 1

        has_cn = sum(1 for a in anime_list if a.get("name_cn"))
        has_date = sum(1 for a in anime_list if a.get("air_date") and len(a.get("air_date", "")) >= 8)
        has_eps = sum(1 for a in anime_list if a.get("episodes"))
        has_studio = sum(1 for a in anime_list if a.get("studio"))

        stats["coverage"] = {
            "chinese_title": f"{has_cn}/{len(anime_list)} ({has_cn/len(anime_list)*100:.1f}%)",
            "air_date": f"{has_date}/{len(anime_list)} ({has_date/len(anime_list)*100:.1f}%)",
            "episodes": f"{has_eps}/{len(anime_list)} ({has_eps/len(anime_list)*100:.1f}%)",
            "studio": f"{has_studio}/{len(anime_list)} ({has_studio/len(anime_list)*100:.1f}%)",
        }

        return stats
