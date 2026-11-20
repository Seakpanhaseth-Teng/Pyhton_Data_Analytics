# The Zero-Cost Stack

Every tool in this engagement is free and open source. Nothing here needs a
licence, a card, a trial, or a "contact sales". Where a free tier has a limit,
it is stated. Verify current limits before you rely on them — vendors move them.

## 1. What the engagement actually uses

| Layer | Tool | Licence | Cost | Notes |
|---|---|---|---|---|
| Language | Python 3.11+ | PSF | Free | Already installed |
| Data wrangling | pandas, numpy | BSD-3 | Free | |
| Database | DuckDB | MIT | Free | In-process OLAP, no server |
| Excel output | openpyxl, xlsxwriter | MIT / BSD | Free | |
| Charts | matplotlib | PSF-based | Free | |
| Version control | Git + GitHub | GPL-2 / SaaS | Free | Unlimited public + private repos |
| Editor | VS Code | Free binary | Free | Alternatives: PyCharm CE, Neovim |
| Notes | Obsidian | Proprietary | Free for personal | Paid only for commercial use |
| Spreadsheet viewer | LibreOffice Calc | MPL-2.0 | Free | Opens the pack without Office |
| Diagramming | Excalidraw, draw.io | MIT / Apache | Free | For process maps and ERDs |

That is the entire required stack. Total cost: **$0**.

## 2. Databases — all free

| Option | Cost | When to use it |
|---|---|---|
| **DuckDB** | Free, local, no server | Default. Reads CSV/Parquet/Excel directly. Fast on your laptop. |
| **SQLite** | Free, public domain | Tiny datasets, mobile. Weaker analytics SQL (no window frames in old builds). |
| **PostgreSQL** | Free, self-host | When you need to practise real server admin, roles, transactions. |
| **Neon** (hosted Postgres) | Free tier ~0.5 GB | Serverless Postgres in the cloud, no install. |
| **Supabase** | Free tier ~500 MB | Postgres + auth + REST API, if you want an "app" feel. |
| **BigQuery** | Free tier: ~1 TB queried/mo, 10 GB storage | Practise real warehouse SQL on public datasets. |
| **MotherDuck** | Free tier | Cloud DuckDB, if you want the same SQL in the browser. |

**Pick DuckDB.** It is the only one that gives you warehouse-grade SQL with zero
installation, zero credentials, and zero latency on a laptop. You can migrate to
Postgres later without relearning much.

## 3. BI and dashboards — the free/paid trap

This is where people accidentally spend money.

| Tool | Cost | Reality check |
|---|---|---|
| **Looker Studio** | Free | Genuinely free, including sharing. Best free "traditional BI" option. Google account required. |
| **Evidence.dev** | Free (MIT) | BI as code — Markdown + SQL → static site. Perfect fit for this repo. |
| **Apache Superset** | Free (Apache-2.0) | Self-host only. Powerful, needs Docker/ops effort. |
| **Metabase OSS** | Free (AGPL) | Self-host, friendlier than Superset, still needs a server. |
| **Streamlit** | Free (Apache-2.0) | Python → app in 30 lines. Not a BI tool, but great for internal tools. |
| **Grafana** | Free (AGPL) | Time-series/ops dashboards. Usable for daily KPIs, awkward for month-end packs. |
| **Power BI Desktop** | Free | **Building** is free. **Publishing/sharing** requires Pro at ~$14/user/month. |
| **Tableau** | Paid | Tableau Public is free but every workbook and its data are public. |

> **The trap:** Power BI Desktop is free, so it feels free — then the moment you
> need to send the report to your manager, you need Pro licences for everyone.
> If the goal is "learn without paying", build in **Looker Studio** or
> **Evidence** and keep Power BI Desktop as an optional resume skill.

## 4. Hosting — free tiers that are actually usable

| Host | Free tier | Good for |
|---|---|---|
| **GitHub Pages** | Static sites, ~1 GB, generous bandwidth | Evidence dashboards, plain HTML reports |
| **Cloudflare Pages** | Static, generous free tier | Same, with better global CDN |
| **Streamlit Community Cloud** | Public apps, ~1 GB RAM | Streamlit apps, sleeps when idle |
| **Hugging Face Spaces** | Free CPU spaces | Demos, portfolio pieces |
| **Render** | Free web services (sleep after idle) | A small API or dashboard |
| **Vercel / Netlify** | Free hobby tier | Static + serverless functions |

**For this project:** export the dashboard as static HTML → push to **GitHub
Pages**. It is permanent, free, and linkable in a CV. No server to maintain.

## 5. Automation — making it "recurring"

An MIS pack that a human has to remember to run is not MIS. Schedule it free:

| Option | Cost | Notes |
|---|---|---|
| **GitHub Actions** | ~2,000 min/month private, unlimited on public repos | Best choice. Cron schedule, runs the pipeline, commits the artifact. |
| **Windows Task Scheduler** | Free, built in | Good for local-only practice. |
| **cron** (WSL/Linux) | Free | If you prefer a POSIX environment. |

GitHub Actions makes the "recurring pack" story real: the workflow file *is* the
answer to "how does this run every month?" in an interview.

## 6. Free learning resources that are actually good

| Need | Resource |
|---|---|
| SQL from zero to window functions | SQLBolt (free), Mode SQL Tutorial (free), PG Exercises (free) |
| Real-world dataset practice | Kaggle Datasets + Notebooks (free) |
| pandas reference | Official pandas "10 minutes" + cookbook (free) |
| Visual design of reports | Storytelling with Data blog (free articles) |
| Interview practice | DataLemur free tier, StrataScratch free tier |
| Free compute | Google Colab free tier, Kaggle Notebooks |

## 7. What genuinely is not free

- **Excel / Microsoft 365** — paid. Use LibreOffice Calc, or openpyxl output and
  accept that `.xlsx` opens fine in either.
- **Tableau Desktop, Power BI Pro sharing, Alteryx, Snowflake credits** — paid.
- **Microsoft Fabric** — trial only.
- **Looker (the enterprise product)** — paid; *Looker Studio* is the free one.
  Do not confuse them; recruiters do.

## 8. Recommended zero-cost path for this repo

```
Python + pandas        reading and cleaning
DuckDB                 staging and all analytical SQL
openpyxl/xlsxwriter    Excel MIS pack for Finance
matplotlib             charts
Evidence.dev  or  static HTML   dashboard
GitHub Pages           hosting
GitHub Actions         monthly refresh
LibreOffice Calc       verifying the pack opens correctly
```

Every layer is free forever, runs on your existing laptop, and produces work you
can show publicly. Nothing in this path requires a cloud account you might
outgrow.
