#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""季度遍历编排器：按年份和季度收集番剧数据"""

import logging
from typing import List, Dict, Any, Optional

from config import SEASONS, SEASON_ORDER, YEAR_RANGE, BATCH_SAVE_INTERVAL
from bangumi_collector import BangumiClient
from infobox_parser import subject_to_record
from chronology_store import ChronologyStore

logger = logging.getLogger(__name__)


class SeasonBuilder:
    def __init__(self, client: BangumiClient = None, store: ChronologyStore = None,
                 use_cache: bool = True):
        self.client = client or BangumiClient()
        self.store = store or ChronologyStore()
        self.use_cache = use_cache

    def collect_season(self, year: int, season: str) -> List[Dict[str, Any]]:
        """收集单个季度的番剧数据"""
        season_info = SEASONS.get(season)
        if not season_info:
            logger.error(f"未知季度: {season}")
            return []

        season_en = season_info["en"]
        months = season_info["months"]

        if self.use_cache and self.store.has_season_cache(year, season_en):
            logger.info(f"从缓存加载 {year}年{season}")
            return self.store.load_season(year, season_en)

        logger.info(f"开始收集 {year}年{season} (月份: {months})")
        seen_ids = set()
        anime_list = []

        for month in months:
            try:
                subjects = self.client.browse_anime(year, month)
                logger.info(f"  {year}-{month:02d}: 获取 {len(subjects)} 条原始数据")

                for subject in subjects:
                    sid = subject.get("id")
                    if sid and sid in seen_ids:
                        continue
                    if sid:
                        seen_ids.add(sid)

                    record = subject_to_record(subject)
                    if record.get("year") == 0:
                        record["year"] = year
                    if not record.get("season"):
                        record["season"] = season

                    anime_list.append(record)
            except Exception as e:
                logger.error(f"收集 {year}-{month:02d} 失败: {e}")

        anime_list.sort(key=lambda x: (
            x.get("air_date") or "9999",
            x.get("name_jp") or "",
        ))

        self.store.save_season(year, season, anime_list)
        logger.info(f"完成 {year}年{season}: {len(anime_list)} 部番剧")
        return anime_list

    def collect_all(self, start_year: int = None, end_year: int = None,
                    progress_callback=None) -> List[Dict[str, Any]]:
        """收集指定年份范围内所有季度的番剧数据"""
        start_year = start_year or YEAR_RANGE[0]
        end_year = end_year or YEAR_RANGE[1]

        all_anime = []
        total_seasons = (end_year - start_year + 1) * 4
        completed = 0

        for year in range(start_year, end_year + 1):
            for season in SEASON_ORDER:
                completed += 1
                try:
                    season_anime = self.collect_season(year, season)
                    all_anime.extend(season_anime)

                    if progress_callback:
                        progress_callback(completed, total_seasons, year, season, len(season_anime))

                    logger.info(f"进度: {completed}/{total_seasons} - {year}年{season}: {len(season_anime)} 部")
                except Exception as e:
                    logger.error(f"收集 {year}年{season} 失败: {e}")

                if completed % BATCH_SAVE_INTERVAL == 0:
                    self.store.save_all(all_anime)

        path = self.store.save_all(all_anime)
        logger.info(f"全量收集完成: {len(all_anime)} 条, 保存至 {path}")
        return all_anime

    def collect_year(self, year: int) -> List[Dict[str, Any]]:
        """收集单个年份的四季数据"""
        year_anime = []
        for season in SEASON_ORDER:
            season_anime = self.collect_season(year, season)
            year_anime.extend(season_anime)
        return year_anime

    def enrich_details(self, anime_list: List[Dict[str, Any]],
                       fields: List[str] = None) -> List[Dict[str, Any]]:
        """补充番剧详情（放送星期、制作公司等）"""
        from infobox_parser import parse_infobox, WEEKDAY_CN
        from config import WEEKDAY_MAP

        default_fields = fields or ["air_weekday", "studio"]
        updated = 0

        for i, anime in enumerate(anime_list):
            need_enrich = False
            for field in default_fields:
                if not anime.get(field):
                    need_enrich = True
                    break

            if not need_enrich:
                continue

            bid = anime.get("bangumi_id")
            if not bid:
                continue

            try:
                detail = self.client.get_subject_detail(bid)
                if detail:
                    info = parse_infobox(detail)
                    if not anime.get("air_weekday") and info.get("air_weekday"):
                        anime["air_weekday"] = info["air_weekday"]
                    if not anime.get("studio") and info.get("studio"):
                        anime["studio"] = info["studio"]
                    if not anime.get("director") and info.get("director"):
                        anime["director"] = info["director"]
                    if not anime.get("episodes") and info.get("episodes_detail"):
                        anime["episodes"] = info["episodes_detail"]
                    updated += 1

                    if (i + 1) % 20 == 0:
                        logger.info(f"详情补充进度: {i+1}/{len(anime_list)}, 已更新: {updated}")
            except Exception as e:
                logger.debug(f"获取详情 {bid} 失败: {e}")

        logger.info(f"详情补充完成: 更新 {updated}/{len(anime_list)} 条")
        return anime_list
