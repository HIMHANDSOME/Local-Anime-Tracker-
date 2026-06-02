#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bangumi API 客户端"""

import json
import os
import time
import hashlib
import logging
import requests
from typing import List, Dict, Any, Optional

from config import (
    BANGUMI_API_BASE, BANGUMI_HEADERS, REQUEST_DELAY,
    MAX_RETRIES, RETRY_BACKOFF, PAGE_SIZE, ANIME_TYPE, RAW_DIR,
)

logger = logging.getLogger(__name__)


class BangumiClient:
    def __init__(self, delay: float = REQUEST_DELAY):
        self.delay = delay
        self._last_request_time = 0.0
        self.session = requests.Session()
        self.session.headers.update(BANGUMI_HEADERS)
        os.makedirs(RAW_DIR, exist_ok=True)

    def _wait(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
        self._last_request_time = time.time()

    def _cache_path(self, endpoint: str, params: dict) -> str:
        key = hashlib.md5(
            f"{endpoint}:{json.dumps(params, sort_keys=True)}".encode()
        ).hexdigest()
        return os.path.join(RAW_DIR, f"api_{key}.json")

    def _request(self, method: str, endpoint: str,
                 params: dict = None, data: dict = None,
                 use_cache: bool = True) -> Optional[dict]:
        url = f"{BANGUMI_API_BASE}{endpoint}"
        cache_file = self._cache_path(endpoint, params or {})

        if use_cache and os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        for attempt in range(MAX_RETRIES):
            self._wait()
            try:
                resp = self.session.request(
                    method, url, params=params, json=data, timeout=20
                )
                if resp.status_code == 200:
                    result = resp.json()
                    if use_cache:
                        try:
                            with open(cache_file, "w", encoding="utf-8") as f:
                                json.dump(result, f, ensure_ascii=False)
                        except Exception:
                            pass
                    return result
                elif resp.status_code == 429:
                    wait = RETRY_BACKOFF * (2 ** attempt)
                    logger.warning(f"429 限速，等待 {wait}s...")
                    time.sleep(wait)
                elif resp.status_code == 404:
                    logger.debug(f"404: {url}")
                    return None
                else:
                    logger.warning(f"HTTP {resp.status_code}: {resp.text[:100]}")
                    if attempt < MAX_RETRIES - 1:
                        time.sleep(RETRY_BACKOFF)
            except requests.exceptions.Timeout:
                logger.warning(f"请求超时: {endpoint}")
            except Exception as e:
                logger.error(f"请求异常: {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_BACKOFF)

        return None

    def browse_anime(self, year: int, month: int, cat: int = None,
                     limit: int = PAGE_SIZE) -> List[Dict[str, Any]]:
        """按月浏览番剧，自动分页"""
        all_subjects = []
        offset = 0

        while True:
            params = {
                "type": ANIME_TYPE,
                "year": year,
                "month": month,
                "limit": limit,
                "offset": offset,
            }
            if cat is not None:
                params["cat"] = cat

            result = self._request("GET", "/v0/subjects", params=params)
            if not result:
                break

            subjects = result.get("data", [])
            total = result.get("total", 0)
            all_subjects.extend(subjects)

            offset += limit
            if offset >= total or not subjects:
                break

        return all_subjects

    def get_subject_detail(self, subject_id: int) -> Optional[Dict[str, Any]]:
        """获取番剧详情"""
        return self._request("GET", f"/v0/subjects/{subject_id}", use_cache=True)

    def search_anime(self, keyword: str, air_date_start: str = None,
                     air_date_end: str = None) -> List[Dict[str, Any]]:
        """搜索番剧"""
        data = {
            "keyword": keyword,
            "filter": {"type": [ANIME_TYPE]},
            "limit": 5,
        }
        if air_date_start or air_date_end:
            date_filter = {}
            if air_date_start:
                date_filter[">="] = air_date_start
            if air_date_end:
                date_filter["<="] = air_date_end
            data["filter"]["air_date"] = date_filter

        result = self._request("POST", "/v0/search/subjects", data=data, use_cache=False)
        if not result:
            return []
        return result.get("data", [])
