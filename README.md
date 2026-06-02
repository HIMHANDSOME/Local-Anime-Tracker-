<div align="center">

# Local Anime Tracker

### 追番手账 — 你的本地番剧档案馆

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.x-green.svg)](https://flask.palletsprojects.com)
[![Bangumi](https://img.shields.io/badge/Data-Bangumi_API-orange.svg)](https://bangumi.github.io/api/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**21,087 titles · 1975–2026 · All stored locally**

[中文文档](README_CN.md)

</div>

---

What if you could own every anime season from the past 50 years — searchable, sortable, and yours to keep?

Local Anime Tracker pulls data from [Bangumi](https://bgm.tv), organizes it by **Year → Season → Title**, and gives you a gorgeous Web UI to browse, track, and export your anime universe. No cloud, no account, no tracking — just you and 21,000+ anime on your own machine.

## Highlights

- **One-command collection** — Pull 50 years of anime data from Bangumi API, with resume support
- **Dual-theme Web UI** — Cyberpunk dark mode with cyan-purple glow, or a fresh light mode with sky-blue & pink
- **Smart browsing** — Filter by year/season/type/status, sort by 9 fields, instant search in Japanese & Chinese
- **Watch tracking** — Mark titles as Want to Watch / Watching / Watched / On Hold / Dropped — persisted locally
- **Excel export** — Color-coded multi-sheet workbook, one sheet per year, high-score highlights
- **All local** — JSON cache + SQLite-free, your data never leaves your machine

## Quick Start

> **Note:** Bangumi API requires network access. Use a VPN if you're outside China.

```bash
# Install dependencies
pip install flask requests openpyxl pandas

# Launch the Web UI
python app.py
```

Open `http://localhost:5000` and you're in.

## Web UI Tour

### Dashboard

Stats at a glance: total count, year range, coverage rates, plus a bar chart of anime per year and donut charts for season & category distribution.

### Browse

The heart of the app. Filter by year, season (January / April / July / October), type (TV/OVA/Movie/WEB), and watch status. Dropdowns auto-trigger search — no click needed. Sort by any of 9 fields with ascending/descending toggle.

Every row has an inline watch-status selector. Changes are saved to the local cache instantly.

### Collect

Set a year range, hit start, and watch the progress bar fill in real-time via SSE. Supports resume — if interrupted, re-run picks up where it left off.

### Export

One click to generate a full Excel chronology. Or split by year into separate files. Download previous exports anytime.

### Dual Themes

| Mode | Vibe | Colors |
|------|------|--------|
| Dark (default) | Cyberpunk / Hacker | Cyan-blue `#7aa2f7` + Purple `#bb9af7` on deep black |
| Light | Clean & Modern | Sky-blue `#5bcffa` + Pink `#f5abb9` on white |

Toggle with the moon/sun button in the sidebar. The sidebar itself collapses and expands — your layout preference persists across sessions.

## CLI

For when you'd rather type than click:

```bash
# Collect everything (1975–2026)
python run_chronology.py collect

# Collect a specific range
python run_chronology.py collect --start-year 2020 --end-year 2026

# One year only
python run_chronology.py collect --year 2024

# Force re-fetch (ignore cache)
python run_chronology.py collect --no-cache

# Enrich with details (broadcast day, studio)
python run_chronology.py collect --enrich

# Export to Excel
python run_chronology.py export

# Export by year (one file per year)
python run_chronology.py export --by-year

# Quick sanity check
python run_chronology.py test
```

## Excel Output

A single workbook with 54 sheets:

- **Overview** — Per-year anime count across all four seasons
- **1975–2026** — One sheet per year, grouped by season with color-coded headers
- **All Data** — Flat table for sorting and filtering

Season headers use color coding: blue for January, green for April, yellow for July, orange for October. Titles rated ≥8.0 get a green highlight.

| Season | Months |
|--------|--------|
| January | Jan–Mar |
| April | Apr–Jun |
| July | Jul–Sep |
| October | Oct–Dec |

## Data Schema

Each record contains:

| Field | Description |
|-------|-------------|
| `name_jp` | Original Japanese title |
| `name_cn` | Chinese translated title |
| `category` | TV / OVA / Movie / WEB |
| `episodes` | Episode count |
| `air_date` | Broadcast start date |
| `air_weekday` | Broadcast weekday |
| `studio` | Production studio |
| `score` | Bangumi rating |
| `watch_status` | Your personal status |

## Project Structure

```
├── app.py                    # Flask Web UI
├── config.py                 # Configuration & constants
├── bangumi_collector.py      # Bangumi API client
├── infobox_parser.py         # Infobox field parser
├── season_builder.py         # Season-based collection orchestrator
├── chronology_store.py       # Data storage & caching
├── chronology_exporter.py    # Excel export engine
├── run_chronology.py         # CLI entry point
├── templates/                # Jinja2 templates
├── static/style.css          # Dual-theme stylesheet
├── data/bangumi/             # Cached data (JSON)
└── output/                   # Exported Excel files
```

## Data Source

All data comes from the [Bangumi API](https://bangumi.github.io/api/):

- `GET /v0/subjects?type=2&year=Y&month=M` — Browse anime by month
- `GET /v0/subjects/{id}` — Fetch detail (broadcast day, studio, etc.)

Requests are rate-limited to 1.5s intervals with automatic 429 retry. A full collection takes ~30 minutes.

## License

MIT
