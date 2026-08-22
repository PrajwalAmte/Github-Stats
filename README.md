# GitHub Stats

[![CI](https://github.com/PrajwalAmte/Github-Stats/actions/workflows/ci.yml/badge.svg)](https://github.com/PrajwalAmte/Github-Stats/actions/workflows/ci.yml)
[![Sync](https://github.com/PrajwalAmte/Github-Stats/actions/workflows/sync.yml/badge.svg)](https://github.com/PrajwalAmte/Github-Stats/actions/workflows/sync.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Generate dynamic GitHub statistics cards for your profile README. Fast, reliable, and free to deploy.

![Profile Stats](https://github-stats-green-one.vercel.app/v1/users/PrajwalAmte/cards/profile.svg)
![Contribution Streak](https://github-stats-green-one.vercel.app/v1/users/PrajwalAmte/cards/streak.svg)
![Top Languages](https://github-stats-green-one.vercel.app/v1/users/PrajwalAmte/cards/languages.svg)

## Usage

### Add to Your README

```markdown
![Stats](https://YOUR-DEPLOYMENT-URL/v1/users/YOUR-USERNAME/cards/profile.svg)
![Streak](https://YOUR-DEPLOYMENT-URL/v1/users/YOUR-USERNAME/cards/streak.svg)
![Languages](https://YOUR-DEPLOYMENT-URL/v1/users/YOUR-USERNAME/cards/languages.svg)
```

### API Endpoints

```bash
# Statistics JSON
GET /v1/users/{username}/stats
GET /v1/users/{username}/languages
GET /v1/users/{username}/history

# SVG Cards
GET /v1/users/{username}/cards/profile.svg
GET /v1/users/{username}/cards/streak.svg
GET /v1/users/{username}/cards/languages.svg
```

## Deployment Guide

### Step 1: Create GitHub Token

1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
2. Generate token with scopes: `read:user`, `repo`
3. Copy the token

### Step 2: Setup Supabase Database

1. Create account at [supabase.com](https://supabase.com) and create new project
2. Go to Project Settings > Database > Connection string
3. Copy **Transaction pooler** (port 6543, NOT 5432)
4. Format: `postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres`

### Step 3: Deploy to Vercel

```bash
# Clone repository
git clone https://github.com/PrajwalAmte/Github-Stats.git
cd Github-Stats

# Install dependencies
pip install -r requirements.txt

# Setup database
cp .env.example .env
# Edit .env: add DATABASE_URL, GITHUB_TOKEN, generate SYNC_SECRET
alembic upgrade head

# Deploy
npm install -g vercel
vercel login
vercel --prod
```

### Step 4: Configure Vercel

In Vercel dashboard > Settings > Environment Variables, add:

- `DATABASE_URL` - Your Supabase transaction pooler URL
- `GITHUB_TOKEN` - Your GitHub token
- `SYNC_SECRET` - Generate with `openssl rand -hex 32`

Redeploy after adding variables.

### Step 5: Setup Auto-Sync

In GitHub repo > Settings > Secrets and variables > Actions, add:

- `API_URL` - Your Vercel URL (e.g., `https://your-app.vercel.app`)
- `SYNC_SECRET` - Same as Vercel

### Step 6: Run First Sync

```bash
curl -X POST "https://your-app.vercel.app/v1/sync/YOUR_USERNAME" \
  -H "Authorization: Bearer YOUR_SYNC_SECRET"
```

Or trigger from: GitHub Actions tab > Sync GitHub Stats > Run workflow

### Step 7: Add Cards to Your README

Replace `YOUR-DEPLOYMENT-URL` and `YOUR-USERNAME`:

```markdown
![Stats](https://YOUR-DEPLOYMENT-URL/v1/users/YOUR-USERNAME/cards/profile.svg)
![Streak](https://YOUR-DEPLOYMENT-URL/v1/users/YOUR-USERNAME/cards/streak.svg)
![Languages](https://YOUR-DEPLOYMENT-URL/v1/users/YOUR-USERNAME/cards/languages.svg)
```

## Troubleshooting

### Connection Issues
- Use **Transaction pooler** URL (port 6543, ends with `.pooler.supabase.com`)
- Verify environment variables in Vercel dashboard

### Sync Fails
- Check `GITHUB_TOKEN` has `read:user` and `repo` scopes
- Ensure database migrations ran: `alembic upgrade head`

### Cards Not Showing
- Run initial sync: `POST /v1/sync/{username}` with auth header
- Verify `/ready` endpoint returns `data_available: true`

### Actions Not Running
- Check GitHub repo secrets: `API_URL` and `SYNC_SECRET`
- Manually trigger workflow from Actions tab to test

## Tech Stack

Python 3.12 • FastAPI • PostgreSQL • SQLAlchemy • Supabase • Vercel

## License

MIT
