# Crunefe Web Crawler

An intelligent command-line web crawler that checks **how crawlable a website is** before scraping it, detects whether the site needs a headless browser, finds RSS feeds and open API endpoints, extracts news articles, and shows the results in a **Streamlit dashboard**.

Built as an Information Retrieval course project by **Lujain Elghamry, Omar Salman and Adham Mostafa**.

---

## Table of contents

- [What it does](#what-it-does)
- [How it works](#how-it-works)
- [Project structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Crawlability scoring](#crawlability-scoring)
- [Output files](#output-files)
- [Known limitations](#known-limitations)
- [Team](#team)
- [License](#license)

---

## What it does

| Feature | Description |
|---|---|
| **robots.txt analysis** | Downloads and parses a site's `robots.txt` (user agents, allow/disallow rules, crawl delay, sitemaps, host) and turns it into a 0–100 crawlability score with a written explanation. |
| **JavaScript-heavy detection** | Fetches the raw HTML with `aiohttp`, renders the same page in headless Chromium with Playwright, and compares the two sizes. If the rendered page is more than 1.5× the raw HTML, the site is flagged as JavaScript-heavy. |
| **RSS feed discovery** | Scans `<link>` tags for `application/rss+xml` and `application/atom+xml` feeds. |
| **Open API discovery** | Probes common API paths (`/api`, `/api/v1`, `/swagger`, `/openapi.json`, `/graphql`, `/wp-json`, …) in parallel and reports the ones that return JSON. |
| **News extraction** | Scrapes article cards from Reuters section pages (`/world/`, `/markets/`, `/breakingviews/`, `/sports/formula1/`), follows each article, and collects title, URL, publish time, lead image and body text into a CSV. |
| **Dashboard** | A Streamlit app that previews the extracted articles, charts articles per day, and shows the latest crawlability score. |

## How it works

```
                ┌──────────────────────┐
                │      main.py (CLI)   │
                └──────────┬───────────┘
         ┌─────────────────┼──────────────────────┐
         ▼                 ▼                      ▼
  1. Analyze site    2. Extract data        3. Open dashboard
         │                 │                      │
  rparser.py         extractor.py           dashbo.py (Streamlit)
  robots.txt  ──►    Reuters scraper  ──►   reads the CSV + score JSON
  score              requests + BS4
         │                 │
  jsAPInew.py              ▼
  JS / RSS / API     reuters_news_extended.csv
  checks
         │
         ▼
  crawlability_score.json
```

1. **Analyze** – `rparser.py` scores the site's `robots.txt` and writes the score to `crawlability_score.json`. `jsAPInew.py` then runs the JavaScript, RSS and API checks concurrently with `asyncio`.
2. **Extract** – `extractor.py` scrapes the news sections with polite random delays (0.5–1.5 s between articles, 2–4 s between pages) and retries failed requests up to 3 times.
3. **Visualize** – `dashbo.py` loads both output files and renders the dashboard.

## Project structure

```
.
├── main.py                     # Interactive CLI menu that ties everything together
├── rparser.py                  # robots.txt parser + crawlability scoring
├── jsAPInew.py                 # JS-heavy detection, RSS feed and open-API discovery (async)
├── extractor.py                # Reuters news article extractor (requests + BeautifulSoup)
├── dashbo.py                   # Streamlit dashboard
├── reuters_news_extended.csv   # Sample output from the extractor
├── requirements.txt            # Python dependencies
└── LICENSE                     # MIT License
```

## Installation

Requires **Python 3.10+** (developed on Python 3.13).

```bash
git clone https://github.com/adhamelsonny014-dot/crunefe-web-crawler.git
cd crunefe-web-crawler
python -m pip install -r requirements.txt
python -m playwright install chromium
```

## Usage

Run the CLI:

```bash
python main.py
```

You'll see this menu:

```
1. Analyze site
2. Extract Data
3. Open Dashboard
4. Exit
```

- **1. Analyze site** – enter a URL such as `https://www.reuters.com`. You get the robots.txt report, score breakdown, and the JavaScript/RSS/API results.
- **2. Extract Data** – enter the base URL (`https://www.reuters.com`) to scrape the news sections into `reuters_news_extended.csv`.
- **3. Open Dashboard** – launches the Streamlit dashboard.

Each module can also be run on its own:

```bash
python extractor.py            # scrape Reuters directly
python -m streamlit run dashbo.py
```

## Crawlability scoring

Every site starts at **100** and is adjusted from its `robots.txt`:

| Rule | Effect |
|---|---|
| `Disallow: /` for all user agents | −40 |
| Each other default `Disallow` rule | −3 |
| Crawl delay > 5 s / > 1 s / ≤ 1 s | −30 / −15 / −5 |
| Googlebot, Bingbot or YandexBot fully blocked | −10 each (max −30) |
| Each sitemap listed | +5 (max +15) |
| Each explicit `Allow` rule | +2 (max +10) |
| Empty or rule-free robots.txt | 100 (fully permissive) |

The final score is kept between 0 and 100 and interpreted as:

| Score | Meaning |
|---|---|
| 90–100 | Very crawler-friendly |
| 70–89 | Crawler-friendly with some restrictions |
| 50–69 | Moderately restrictive |
| 30–49 | Significantly restrictive |
| 0–29 | Highly restrictive / blocking most crawlers |

## Output files

| File | Written by | Contents |
|---|---|---|
| `crawlability_score.json` | Analyze site | `{"score": <0-100>}` for the last analyzed site |
| `reuters_news_extended.csv` | Extract data | `title, url, time, image_url, content` for each article |

## Known limitations

- The extractor's CSS selectors target Reuters' current HTML. If Reuters changes its markup, update the `SELECTORS` dictionary at the top of `extractor.py`.
- The CLI clears the screen with `cls`, so it's designed for Windows terminals.
- Respect each site's terms of service and `robots.txt` when crawling.

## Team

| Member | Role |
|---|---|
| **Adham Mostafa** | Crawlability specialist and JS/API handler |
| **Lujain Elghamry** | Content extractor |
| **Omar Salman** | Dashboard and GitHub |

## License

This project is licensed under the [MIT License](LICENSE).
