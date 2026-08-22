# Deployment Guide

This guide walks you through deploying the GitHub Stats Service to production.

## Prerequisites

- [ ] Supabase account (or any PostgreSQL provider)
- [ ] Vercel account
- [ ] GitHub account (for Actions scheduler)
- [ ] GitHub Personal Access Token

---

## Step 1: Database Setup (Supabase)

1. **Create a Supabase project**:
   - Go to [supabase.com](https://supabase.com)
   - Click "New Project"
   - Choose a name and region
   - Set a strong database password

2. **Get connection strings**:
   - Go to Project Settings → Database
   - Copy the "Connection pooling" URL (important for serverless!)
   - Format: `postgresql://postgres:[PASSWORD]@[HOST]:6543/postgres?pgbouncer=true`

3. **Run migrations locally first** (recommended):
   ```bash
   # Set DATABASE_URL in .env with your Supabase URL
   alembic upgrade head
   ```
   
   Or run migrations from Supabase SQL Editor:
   - Copy contents of `migrations/versions/001_initial_schema.py`
   - Execute the SQL in the `upgrade()` function

---

## Step 2: GitHub Token Setup

1. **Create Personal Access Token**:
   - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token (classic)"
   - Give it a descriptive name: "GitHub Stats Service"
   - Select scopes:
     - `read:user` - Read profile information
     - `public_repo` - Read public repository data
   - Click "Generate token"
   - **Copy the token immediately** - you won't see it again!

2. **Token format**: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

## Step 3: Vercel Deployment

1. **Install Vercel CLI** (optional but recommended):
   ```bash
   npm install -g vercel
   ```

2. **Deploy from CLI**:
   ```bash
   cd github-stats
   vercel
   ```
   
   Or deploy from Vercel dashboard:
   - Go to [vercel.com/new](https://vercel.com/new)
   - Import your GitHub repository
   - Framework preset: Other
   - Build command: (leave empty)
   - Output directory: (leave empty)

3. **Configure Environment Variables** in Vercel:
   
   Go to Project Settings → Environment Variables and add:
   
   | Variable | Value | Notes |
   |----------|-------|-------|
   | `DATABASE_URL` | Your Supabase connection string | Use "Connection pooling" URL |
   | `GITHUB_TOKEN` | Your GitHub personal access token | Starts with `ghp_` |
   | `SYNC_SECRET` | Random 64-character hex string | Generate with: `openssl rand -hex 32` |
   | `ENVIRONMENT` | `production` | Optional |
   | `LOG_LEVEL` | `INFO` | Optional |

4. **Deploy**:
   ```bash
   vercel --prod
   ```

5. **Note your deployment URL**: `https://your-project.vercel.app`

---

## Step 4: Test the Deployment

1. **Check health**:
   ```bash
   curl https://your-project.vercel.app/health
   ```

2. **Manual sync** (to populate initial data):
   ```bash
   curl -X POST https://your-project.vercel.app/v1/sync/PrajwalAmte \
     -H "Authorization: Bearer YOUR_SYNC_SECRET"
   ```
   
   Replace `YOUR_SYNC_SECRET` with the value you set in Vercel.

3. **Verify data**:
   ```bash
   curl https://your-project.vercel.app/v1/users/PrajwalAmte/stats
   ```

4. **Test SVG cards** in browser:
   - `https://your-project.vercel.app/v1/users/PrajwalAmte/cards/profile.svg`
   - `https://your-project.vercel.app/v1/users/PrajwalAmte/cards/streak.svg`

---

## Step 5: GitHub Actions Scheduler

1. **Add repository secrets**:
   - Go to your GitHub repository
   - Settings → Secrets and variables → Actions
   - Click "New repository secret"
   
   Add these secrets:
   
   | Secret | Value |
   |--------|-------|
   | `API_URL` | Your Vercel deployment URL (without trailing slash) |
   | `SYNC_SECRET` | Same value as in Vercel |

2. **Workflow is already configured** in `.github/workflows/sync.yml`

3. **Test manual trigger**:
   - Go to Actions tab
   - Select "Sync GitHub Stats" workflow
   - Click "Run workflow"
   - Enter username or leave default
   - Click "Run workflow"

4. **Verify schedule**:
   - The workflow runs automatically every 3 hours
   - Check Actions tab for execution history

---

## Step 6: Update Your README

Add the SVG cards to your GitHub profile README:

```markdown
## 📊 GitHub Statistics

![GitHub Stats](https://your-project.vercel.app/v1/users/PrajwalAmte/cards/profile.svg)
![Streak Stats](https://your-project.vercel.app/v1/users/PrajwalAmte/cards/streak.svg)
```

Replace:
- `your-project.vercel.app` with your actual Vercel domain
- `PrajwalAmte` with your GitHub username

---

## Monitoring and Maintenance

### Check Sync Status

```bash
curl https://your-project.vercel.app/v1/users/PrajwalAmte/stats | jq '.meta'
```

Look for:
- `last_sync`: When data was last updated
- `sync_status`: Should be `"ok"`

### View GitHub Actions Logs

1. Go to your repository
2. Click Actions tab
3. Click on a workflow run
4. View logs for sync results

### Troubleshooting

**Sync fails with 401**:
- Check GitHub token is valid
- Verify token has correct scopes

**Sync fails with database error**:
- Verify DATABASE_URL is correct
- Check Supabase project is active
- Ensure you're using the "Connection pooling" URL

**Cards show stale data**:
- Check `last_sync` timestamp in API response
- Review GitHub Actions logs for failures
- Manually trigger sync via Actions

**429 Rate limit errors**:
- GitHub has API rate limits
- Authenticated requests: 5,000/hour
- Check your usage: `curl https://api.github.com/rate_limit -H "Authorization: Bearer YOUR_TOKEN"`

---

## Cost Estimation

### Free Tier Usage

- **Vercel**: 100GB bandwidth/month, unlimited API requests (Hobby plan)
- **Supabase**: 500MB database, 2GB bandwidth/month (Free plan)
- **GitHub Actions**: 2,000 minutes/month (Free for public repos)

### Expected Usage (Single User, Every 3 Hours)

- **API requests**: ~240 syncs/month × ~3 GitHub API calls = ~720 calls
- **Database**: ~10MB (one user, one year of data)
- **Actions**: ~240 minutes/month
- **Bandwidth**: ~1GB/month (depends on card views)

**Result**: Easily fits within free tiers for personal use.

---

## Security Best Practices

1. **Never commit secrets**:
   - `.env` is in `.gitignore`
   - Always use environment variables

2. **Rotate tokens periodically**:
   - GitHub tokens should be rotated every 6-12 months
   - Update in Vercel environment variables

3. **Use read-only GitHub token**:
   - Never give write permissions
   - Only `read:user` and `public_repo` scopes

4. **Secure sync endpoint**:
   - `SYNC_SECRET` should be cryptographically random
   - Never expose in client-side code

5. **Monitor for anomalies**:
   - Check GitHub Actions logs weekly
   - Review Vercel analytics for unusual traffic

---

## Scaling Considerations

### Multiple Users

To track multiple GitHub users:

1. **Update GitHub Actions workflow**:
   ```yaml
   - name: Sync Multiple Users
     run: |
       for user in PrajwalAmte user2 user3; do
         curl -X POST "${{ secrets.API_URL }}/v1/sync/$user" \
           -H "Authorization: Bearer ${{ secrets.SYNC_SECRET }}"
       done
   ```

2. **Database growth**:
   - Each user adds ~5-10MB per year
   - Supabase free tier: 500MB (50-100 users)

3. **GitHub API rate limits**:
   - 5,000 requests/hour with authentication
   - ~30 users comfortably with 3-hour sync interval

### High Traffic

If your README cards get significant traffic:

1. **Vercel automatically scales** serverless functions
2. **CDN caching** reduces origin hits significantly
3. **Consider upgrading** Vercel plan for more bandwidth
4. **Monitor** Vercel analytics dashboard

---

## Backup Strategy

### Database Backups

Supabase automatically backs up your database daily (retained 7 days on free tier).

**Manual backup**:
```bash
pg_dump $DATABASE_URL > backup.sql
```

### Application Code

- Keep code in Git
- Tag releases: `git tag v1.0.0 && git push --tags`

---

## Updating the Application

1. **Pull latest changes**:
   ```bash
   git pull origin main
   ```

2. **Run new migrations** (if any):
   ```bash
   alembic upgrade head
   ```

3. **Deploy to Vercel**:
   ```bash
   vercel --prod
   ```

Vercel automatically deploys on `git push` if you connected the repository.

---

## Support

If you encounter issues:

1. **Check logs**:
   - Vercel deployment logs
   - GitHub Actions logs
   - Supabase logs

2. **Review documentation**:
   - README.md
   - To-Do.md (architectural constraints)
   - API responses (meta field shows sync status)

3. **Common issues**:
   - 401: Check GitHub token
   - 409: Sync already running (wait for it to finish)
   - 500: Check Vercel logs for details

---

## Success Checklist

- [ ] Database migrations completed
- [ ] Environment variables configured in Vercel
- [ ] Initial manual sync successful
- [ ] API endpoints returning data
- [ ] SVG cards rendering correctly
- [ ] GitHub Actions secrets configured
- [ ] Scheduled workflow running successfully
- [ ] Cards added to GitHub profile README
- [ ] Monitoring set up (optional)

Congratulations! Your GitHub Stats Service is now live! 🎉
