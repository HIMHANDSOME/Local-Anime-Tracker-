<div align="center">

# Local Anime Tracker

### 追番手账 — 你的本地番剧档案馆

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-green.svg)](https://flask.palletsprojects.com)
[![Bangumi](https://img.shields.io/badge/Data-Bangumi_API-orange.svg)](https://bangumi.github.io/api/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**21,087 部 · 1975–2026 · 全部存本地**

[English](README.md)

</div>

---

如果把过去 50 年的每一季新番都装进你自己的电脑——可搜索、可排序、永远属于你，会怎样？

追番手账从 [Bangumi](https://bgm.tv) 拉取动画数据，按 **年份 → 季度 → 番剧** 层级组织，配上精心设计的 Web UI，让你浏览、追踪、导出自己的番剧宇宙。不上云、不注册、不被追踪——你和 21,000+ 部番剧，只隔一台本地服务器。

## 亮点

- **一条命令收集** — 从 Bangumi API 拉取 50 年番剧数据，支持断点续传
- **双主题 Web UI** — 赛博极客暗夜模式（青蓝紫光），清新现代白天模式（天蓝粉白）
- **智能浏览** — 按年份/季度/类型/状态筛选，9 字段排序，日文中文即时搜索
- **观看追踪** — 想看/在看/看过/搁置/抛弃，一键标记，本地持久化
- **Excel 导出** — 色彩分明的多年表工作簿，每年一 Sheet，高分高亮
- **完全本地** — JSON 缓存，无需数据库，数据不出你的电脑

## 快速开始

> **注意：** Bangumi API 需要网络访问，国内请挂梯子。

```bash
# 安装依赖
pip install flask requests openpyxl pandas

# 启动 Web UI
python app.py
```

打开 `http://localhost:5000`，开箱即用。

## Web UI 导览

### 仪表盘

一眼看全局：番剧总数、年份范围、覆盖率，还有年度数量柱状图和季度/类型分布饼图。

### 浏览

核心页面。按年份、季度（一月/四月/七月/十月）、类型（TV/OVA/Movie/WEB）、观看状态筛选。下拉选项选完自动刷新，不用手动点搜索。9 个字段随便排，升序降序自由切。

每行都有内嵌的观看状态选择器，改动即时写回本地缓存。

### 收集

设好年份范围，点击开始，SSE 实时推送进度条和日志。支持断点续传——中断了再跑，自动跳过已缓存的季度。

### 导出

一键生成完整 Excel 年表，也可以按年份拆分导出。历史导出随时下载。

### 双主题

| 模式 | 风格 | 配色 |
|------|------|------|
| 暗夜模式（默认） | 赛博极客 | 青蓝 `#7aa2f7` + 紫 `#bb9af7` + 深黑 |
| 白天模式 | 清新现代 | 天蓝 `#5bcffa` + 粉 `#f5abb9` + 纯白 |

侧栏底部的月亮/太阳按钮一键切换。侧栏本身可以收起展开，布局偏好自动保存到浏览器。

## 命令行

终端党的福音：

```bash
# 收集全部年份（1975–2026）
python run_chronology.py collect

# 收集指定范围
python run_chronology.py collect --start-year 2020 --end-year 2026

# 只收一年
python run_chronology.py collect --year 2024

# 强制重新拉取（忽略缓存）
python run_chronology.py collect --no-cache

# 收集后补充详情（放送星期、制作公司等）
python run_chronology.py collect --enrich

# 导出 Excel
python run_chronology.py export

# 按年份分别导出
python run_chronology.py export --by-year

# 快速验证流程
python run_chronology.py test
```

## Excel 输出

一份工作簿，54 个 Sheet：

- **总览** — 每年四季番剧数量一览表
- **1975–2026** — 每年一个 Sheet，按季度分组，标题行色彩区分
- **全部数据** — 扁平表，支持筛选和排序

季度标题行色彩编码：一月蓝、四月绿、七月黄、十月橙。评分 ≥8.0 的番剧绿色高亮。

| 季度 | 月份 |
|------|------|
| 一月 | 1–3月 |
| 四月 | 4–6月 |
| 七月 | 7–9月 |
| 十月 | 10–12月 |

## 数据字段

每条记录包含：

| 字段 | 说明 |
|------|------|
| `name_jp` | 日文原名 |
| `name_cn` | 中文译名 |
| `category` | TV / OVA / Movie / WEB |
| `episodes` | 集数 |
| `air_date` | 放送开始日期 |
| `air_weekday` | 放送星期 |
| `studio` | 制作公司 |
| `score` | Bangumi 评分 |
| `watch_status` | 个人观看状态 |

## 项目结构

```
├── app.py                    # Flask Web UI
├── config.py                 # 配置与常量
├── bangumi_collector.py      # Bangumi API 客户端
├── infobox_parser.py         # Infobox 字段解析器
├── season_builder.py         # 按季度收集编排器
├── chronology_store.py       # 数据存储与缓存
├── chronology_exporter.py    # Excel 导出引擎
├── run_chronology.py         # CLI 入口
├── templates/                # Jinja2 模板
├── static/style.css          # 双主题样式表
├── data/bangumi/             # 缓存数据（JSON）
└── output/                   # 导出的 Excel 文件
```

## 数据来源

所有数据来自 [Bangumi API](https://bangumi.github.io/api/)：

- `GET /v0/subjects?type=2&year=Y&month=M` — 按月浏览动画
- `GET /v0/subjects/{id}` — 获取详情（放送星期、制作公司等）

请求间隔 1.5 秒，遇 429 自动退避重试，完整收集约 30 分钟。

## 开源协议

MIT
