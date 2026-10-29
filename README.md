# GitHub Stats

[![CI](https://github.com/PrajwalAmte/Github-Stats/actions/workflows/ci.yml/badge.svg)](https://github.com/PrajwalAmte/Github-Stats/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

GitHub stats cards for your profile README that load on the first try. No database, no sync jobs, no setup.

<img alt="GitHub Overview" src="https://github-stats-green-one.vercel.app/v1/users/PrajwalAmte/cards/overview.svg">

## Two ways to use it

### 1. Hosted URL: paste and go

```markdown
![GitHub Stats](https://github-stats-green-one.vercel.app/v1/users/YOUR-USERNAME/cards/overview.svg)
```

Works for any GitHub user right away. There is no sign-up or first sync to wait for.

### 2. GitHub Action: the most reliable option

The cards are rendered on a schedule and committed to **your own repo**, so your README serves them from GitHub itself. No third-party server is involved when someone views your profile. Nothing can be down, rate-limited, or slow.

Add `.github/workflows/stats.yml` to your profile repo (`YOUR-USERNAME/YOUR-USERNAME`):

```yaml
name: Update stats cards
on:
  schedule:
    - cron: "0 */6 * * *"
  workflow_dispatch:

permissions:
  contents: write

jobs:
  cards:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: PrajwalAmte/Github-Stats@main
```

Then reference the files in your README:

```markdown
![GitHub Stats](./github-stats/overview.svg)
```

| Input | Default | |
|---|---|---|
| `username` | repo owner | Whose stats to render |
| `cards` | `overview,profile,streak,languages` | Which cards to write |
| `output-dir` | `github-stats` | Where to write them |
| `token` | `github.token` | Token for the GraphQL API |
| `history` | `true` | Record a daily snapshot in `history.json` |
| `commit` | `true` | Commit and push if anything changed |

Runs that only change the timestamp are skipped, so your history isn't flooded with empty commits.

#### History

Each run also writes the day's stats into `github-stats/history.json`. That gives you a dated record of commits, contributions, streaks, stars and followers, and git serves as the database. The file holds one entry per UTC day; re-running on the same day overwrites that day's entry, so the file grows by at most one entry per day.

```json
{
  "version": 1,
  "username": "octocat",
  "snapshots": [
    { "date": "2026-10-29", "total_commits": 295, "contribution_count": 311,
      "current_streak": 10, "longest_streak": 12, "star_count": 6, "followers": 13, "...": "..." }
  ]
}
```

#### Privacy

Cards and `history.json` contain only aggregate numbers: no repo names, emails or tokens. Repositories are always restricted to **public** ones, so even a token that can read your private repos won't leak their count, stars or languages. Contribution totals (commits, PRs, streaks) count whatever your token can see. With the default `github.token`, that's what your public profile shows. Set `history: false` if you don't want a dated record kept in git; deleting the file later doesn't remove it from git history.

### Cards

```text
/v1/users/{username}/cards/overview.svg
/v1/users/{username}/cards/profile.svg
/v1/users/{username}/cards/streak.svg
/v1/users/{username}/cards/languages.svg
```

### JSON

```text
/v1/users/{username}/stats
/v1/users/{username}/languages
```

Contribution counts (commits, PRs, issues, reviews, streaks) cover the last year, matching your GitHub contribution graph.

---

## Why it loads on the first try

GitHub proxies every README image through its image proxy (camo), which gives up on slow responses and shows a broken image. Most stats services are slow on a cold request. This one is built around that:

```mermaid
flowchart LR
    R[README / camo] --> C[Vercel edge cache]
    C -- miss or background refresh --> F[Function]
    F -- one GraphQL query --> G[GitHub]
```

- **Served from the edge.** Cards are cached at the CDN for an hour and kept for a day with `stale-while-revalidate`. Visitors get the cached copy instantly while it refreshes in the background.
- **Fast when the cache is empty.** One GraphQL query fetches everything, with languages included per repo instead of one request per repo. Pagination stops at a ~4s budget, so even accounts with 1,000+ repos render in about 3.5s. (They get stats from their top repos by stars. Use the Action if you want exact totals.)
- **Readable errors.** A missing user or bad URL renders an error card instead of a broken image.
- **Survives GitHub outages.** If GitHub fails when a cached card is due for refresh, the server answers `503`. Vercel's CDN then keeps serving the last good card (`stale-if-error`) for up to a week, instead of replacing it with an error. A card that has never been cached shows a "GitHub unavailable" card. Each warm instance also keeps its last good result as a further fallback.
- **Survives rate limits.** `GITHUB_TOKEN` accepts several comma-separated tokens and moves to the next one when a token is exhausted.

## Self-hosting

Deploy to Vercel and set one environment variable:

```text
GITHUB_TOKEN=ghp_xxx           # a classic PAT with no scopes is enough
                               # several tokens: ghp_a,ghp_b,ghp_c
```

Local development:

```bash
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

## Contributing

Issues and PRs welcome: bug fixes, new card designs, more stats. For larger changes, open an issue first so we can agree on the approach.

## Tech Stack

Python 3.12 · FastAPI · httpx · Vercel

## License

MIT
