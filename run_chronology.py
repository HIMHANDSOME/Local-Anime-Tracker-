#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""番剧年表 CLI 入口"""

import argparse
import logging
import sys

from config import YEAR_RANGE


def setup_logging(level=logging.INFO):
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
        handlers=[
            logging.FileHandler("chronology.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def cmd_collect(args):
    from season_builder import SeasonBuilder
    from chronology_store import ChronologyStore

    builder = SeasonBuilder(use_cache=not args.no_cache)
    store = ChronologyStore()

    start = args.start_year or YEAR_RANGE[0]
    end = args.end_year or YEAR_RANGE[1]

    if args.year:
        start = end = args.year

    print(f"开始收集 {start}-{end} 年番剧数据...")
    anime_list = builder.collect_all(start, end)
    print(f"收集完成: {len(anime_list)} 条")

    if args.enrich:
        print("补充详情中...")
        anime_list = builder.enrich_details(anime_list)
        store.save_all(anime_list)

    stats = store.get_stats(anime_list)
    _print_stats(stats)


def cmd_export(args):
    from chronology_store import ChronologyStore
    from chronology_exporter import ChronologyExporter

    store = ChronologyStore()
    anime_list = store.load_all_from_files()

    if not anime_list:
        print("未找到缓存数据，请先运行 collect")
        return

    print(f"加载 {len(anime_list)} 条数据")

    exporter = ChronologyExporter()
    filepath = exporter.export(anime_list, filename=args.filename)
    if filepath:
        print(f"已导出: {filepath}")

    if args.by_year:
        files = exporter.export_by_year(anime_list)
        print(f"按年份导出 {len(files)} 个文件")


def cmd_stats(args):
    from chronology_store import ChronologyStore

    store = ChronologyStore()
    anime_list = store.load_all_from_files()

    if not anime_list:
        print("未找到缓存数据")
        return

    stats = store.get_stats(anime_list)
    _print_stats(stats)


def cmd_test(args):
    """用 2024 年数据做快速测试"""
    from season_builder import SeasonBuilder
    from chronology_store import ChronologyStore
    from chronology_exporter import ChronologyExporter

    builder = SeasonBuilder(use_cache=not args.no_cache)

    print("测试: 收集 2024 年番剧数据...")
    anime_list = builder.collect_year(2024)
    print(f"2024 年共收集 {len(anime_list)} 部")

    stats = ChronologyStore().get_stats(anime_list)
    _print_stats(stats)

    if args.enrich:
        print("补充详情中...")
        anime_list = builder.enrich_details(anime_list)

    print("导出 Excel...")
    exporter = ChronologyExporter()
    filepath = exporter.export(anime_list, filename="番剧年表_测试2024.xlsx")
    if filepath:
        print(f"测试文件已导出: {filepath}")


def _print_stats(stats):
    if not stats:
        return
    print(f"\n{'='*50}")
    print(f"总计: {stats['total']} 部番剧")
    print(f"\n按年份:")
    for year in sorted(stats["by_year"].keys()):
        print(f"  {year}: {stats['by_year'][year]} 部")
    print(f"\n按季度:")
    for season in ["一月", "四月", "七月", "十月"]:
        if season in stats["by_season"]:
            print(f"  {season}: {stats['by_season'][season]} 部")
    print(f"\n数据覆盖率:")
    for field, coverage in stats.get("coverage", {}).items():
        print(f"  {field}: {coverage}")
    print(f"{'='*50}\n")


def main():
    parser = argparse.ArgumentParser(description="番剧年表制作工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # collect
    p_collect = subparsers.add_parser("collect", help="收集番剧数据")
    p_collect.add_argument("--start-year", type=int, help="起始年份")
    p_collect.add_argument("--end-year", type=int, help="结束年份")
    p_collect.add_argument("--year", type=int, help="只收集指定年份")
    p_collect.add_argument("--no-cache", action="store_true", help="忽略缓存重新收集")
    p_collect.add_argument("--enrich", action="store_true", help="补充详情（放送星期等）")

    # export
    p_export = subparsers.add_parser("export", help="导出 Excel")
    p_export.add_argument("--filename", help="输出文件名")
    p_export.add_argument("--by-year", action="store_true", help="按年份分别导出")

    # stats
    subparsers.add_parser("stats", help="查看数据统计")

    # test
    p_test = subparsers.add_parser("test", help="测试收集 2024 年数据")
    p_test.add_argument("--no-cache", action="store_true")
    p_test.add_argument("--enrich", action="store_true")

    args = parser.parse_args()
    setup_logging()

    if args.command == "collect":
        cmd_collect(args)
    elif args.command == "export":
        cmd_export(args)
    elif args.command == "stats":
        cmd_stats(args)
    elif args.command == "test":
        cmd_test(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
