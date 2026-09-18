# Vercel Deployment Guide

**Note**: Vercel's serverless architecture is optimized for stateless request handlers. For a continuously-running API server like free-claude-code, alternative platforms offer better performance and cost efficiency. This guide covers both Vercel and recommended alternatives.

## Platform Comparison

| Platform | Best For | Cost | Setup Time | Cold Start | Max Duration |
|----------|----------|------|-----------|-----------|--------------|
| **Docker (Local)** | Development | Free | 5 min | Instant | N/A |
| **Railway** | ✅ **Recommended** | $5/mo starter | 2 min | < 100ms | Unlimited |
| **Render** | Production | $7/mo starter | 3 min | < 100ms | Unlimited |
| **Fly.io** | Scale-out | Free tier | 5 min | < 100ms | Unlimited |
| **Vercel** | Web UI only | $20+/mo Pro | 3 min | 2-5s | 60s (Pro) |

---

## Quick Deploy to Railway (Recommended)

Railway is the best platform for free-claude-code because:
- ✅ Runs continuously (no cold starts between requests)
- ✅ Affordable ($5/month starter tier)
- ✅ Simple one-click deployment
- ✅ Free tier available for testing
- ✅ iPhone/iPad deployment via web browser

### Steps:

1. **Connect GitHub**
   - Go to [railway.app](https://railway.app)
   - Click "Start a new Project" → "GitHub Repo"
   - Authorize Railway to access your GitHub
   - Select `sjbrenchley89/free-claude-code`

2. **Configure Environment**
   - Railway auto-detects `pyproject.toml`
   - Add environment variables:
     - `ANTHROPIC_API_KEY`: Your API key from [console.anthropic.com](https://console.anthropic.com/account/keys)
     - `FCC_DEFAULT_MODEL`: `anthropic/claude-3-5-sonnet-20241022`
     - `FCC_PORT`: `8082` (Railway sets PORT automatically; this is for internal reference)

3. **Deploy**
   - Railway auto-deploys on git push
   - Custom domain: Add under Settings → Domain
   - Access at: `https://your-railway-domain.railway.app`

4. **Test from iPhone**
   - Open Safari on iOS
   - Visit: `https://your-railway-domain.railway.app/health`
   - Response: `{"status": "healthy"}`

---

## Deploy to Render

Render is another excellent option with a free tier for testing.

### Steps:

1. **Create Service**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect GitHub and select `sjbrenchley89/free-claude-code`

2. **Configure**
   - **Build Command**: `pip install -U uv && uv sync`
   - **Start Command**: `uv run fcc-server`
   - **Port**: Auto-detected as 8082

3. **Environment Variables**
   - Same as Railway (see above)

4. **Deploy**
   - Render auto-deploys on git push
   - Custom domain available on Starter plan ($7/month)

---

## Deploy to Fly.io

Fly.io offers global deployment with free tier.

### Steps:

1. **Install CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Launch App**
   ```bash
   fly launch --repo sjbrenchley89/free-claude-code
   ```

3. **Configure fly.toml** (auto-generated)
   ```toml
   app = "free-claude-code"
   
   [build]
   builder = "paketobuildpacks"
   
   [env]
   ANTHROPIC_API_KEY = "your-key-here"
   FCC_DEFAULT_MODEL = "anthropic/claude-3-5-sonnet-20241022"
   
   [[services]]
   protocol = "tcp"
   internal_port = 8082
   ```

4. **Deploy**
   ```bash
   fly deploy
   ```

5. **Access**
   ```bash
   fly open /health
   ```

---

## Vercel Deployment (Web UI Only)

If you prefer Vercel for the web interface, deploy the admin dashboard separately while running the API server on Railway/Render.

### Setup:

1. **Fork the repository** (if not already)

2. **Import to Vercel**
   - Go to [vercel.com/new](https://vercel.com/new)
   - Select "Other" as framework
   - Vercel reads `vercel.json`
   - **Note**: The actual server runs on Railway, Render, or your infrastructure

3. **Configure Environment** (for remote server integration)
   - `FCC_API_URL`: https://your-railway-domain.railway.app
   - `FCC_API_TOKEN`: (if authentication enabled)

4. **Deploy**
   - Click "Deploy"
   - Vercel creates a production URL

### Important Limitations:

- Vercel's serverless functions have **60-second timeout** (Pro plan)
- Each request creates a new function instance (cold starts)
- No persistent state between requests
- **Recommended**: Use Vercel only for dashboard/admin UI, host actual API on Railway/Render

---

## Manual Deployment: Static Admin Dashboard on Vercel

To host just the admin dashboard on Vercel while the API runs elsewhere:

1. **Build Admin Assets**
   ```bash
   cd src/free_claude_code/api/admin_static
   npm install
   npm run build
   ```

2. **Create `vercel.json` for static files**
   ```json
   {
     "buildCommand": "npm run build",
     "outputDirectory": "public"
   }
   ```

3. **Deploy**
   ```bash
   vercel --prod
   ```

4. **Configure API Endpoint**
   - In admin dashboard settings, point to: `https://your-railway-domain.railway.app`

---

## iOS Deployment Flow

All platforms support mobile deployment through the browser:

### From iPhone/iPad:

1. **Open Safari**
2. **Navigate to your server URL**: `https://your-railway-domain.railway.app`
3. **Access Admin Panel**: `/admin`
4. **You can now**:
   - View server status
   - Monitor API requests
   - Configure providers
   - Update settings
   - Deploy updates (if using GitHub integration)

### GitHub Actions Mobile Deploy:

For hands-free deployment from iOS:

1. **Push code to GitHub**: Via mobile Git client (Working Copy, GitDown)
2. **GitHub Actions triggers**:
   - Runs CI/CD pipeline
   - Deploys to Railway/Render automatically
   - Notifies via push notification

### Apps for Mobile Development:

| App | Use Case | iOS | Cost |
|-----|----------|-----|------|
| **Working Copy** | Full Git client | ✅ | $14.99 |
| **GitDown** | Simplified Git | ✅ | Free |
| **SSH Files** | SSH terminal | ✅ | $14.99 |
| **Coduo** | Code editor | ✅ | Free |

---

## Monitoring Your Deployment

### Railway Dashboard:
- CPU, Memory, Disk usage graphs
- Real-time logs
- Deployment history
- Rollback capability

### API Health Check:
```bash
curl https://your-railway-domain.railway.app/health
```

### Server Metrics:
```bash
curl https://your-railway-domain.railway.app/metrics
```

### Admin Dashboard:
```
https://your-railway-domain.railway.app/admin
```

---

## Environment Variables Reference

### Required:
- `ANTHROPIC_API_KEY`: From https://console.anthropic.com/account/keys

### Optional Providers:
- `GROQ_API_KEY`: For Groq models
- `OPENROUTER_API_KEY`: For OpenRouter models
- `DEEPSEEK_API_KEY`: For DeepSeek models
- `OPENAI_API_KEY`: For OpenAI models
- `AZURE_OPENAI_API_KEY`: For Azure OpenAI
- `AZURE_OPENAI_BASE_URL`: Azure endpoint

### Server Configuration:
- `FCC_DEFAULT_MODEL`: Default model (default: `anthropic/claude-3-5-sonnet-20241022`)
- `FCC_PORT`: Server port (default: `8082`)
- `FCC_HOST`: Bind address (default: `0.0.0.0`)
- `FCC_LOG_LEVEL`: Log level (default: `INFO`)

### Security:
- `PROXY_AUTH_ENABLED`: Enable API token auth (default: `false`)
- `ANTHROPIC_AUTH_TOKEN`: Auth token (if enabled)

---

## Troubleshooting

### Deployment fails with "Python version not found"
- Ensure `pyproject.toml` specifies `requires-python = ">=3.14.0"`
- Railway/Render will auto-install Python 3.14

### Server times out on Vercel
- **Expected behavior** - Vercel has 60s timeout
- **Solution**: Switch to Railway or Render for API server

### Health check fails
- Verify `ANTHROPIC_API_KEY` is set
- Check logs: `railway logs` or `render logs`
- Test locally first: `uv run fcc-server`

### Admin dashboard doesn't load
- Ensure `/admin` endpoint is accessible
- Check browser console for CORS errors
- Verify API URL in dashboard configuration

---

## Recommended Setup

**For Best Results**: Use this configuration:

```
┌─────────────────────────────────────────┐
│     iOS Safari / Mobile Device          │
└────────────────┬────────────────────────┘
                 │
        ┌────────▼──────────┐
        │  Admin Dashboard  │
        │  (Vercel)         │
        └────────┬──────────┘
                 │ API calls
        ┌────────▼──────────┐
        │  API Server       │
        │  (Railway)        │ ← $5/month
        │  Anthropic Claude │
        └───────────────────┘
```

This setup:
- ✅ Costs only $5/month
- ✅ Deploys from iOS browser
- ✅ No cold starts between requests
- ✅ Automatic updates via GitHub
- ✅ 99.9% uptime SLA
- ✅ Real-time monitoring

---

## Deploy Now

```bash
# Clone the repository
git clone https://github.com/sjbrenchley89/free-claude-code.git
cd free-claude-code

# Option 1: Railway (Recommended)
# 1. Go to railway.app
# 2. Click "Start a new Project"
# 3. Select "Deploy from GitHub repo"
# 4. Choose sjbrenchley89/free-claude-code
# 5. Add ANTHROPIC_API_KEY environment variable
# 6. Deploy!

# Option 2: Render
# 1. Go to render.com
# 2. Click "New Web Service"
# 3. Connect GitHub and select repository
# 4. Set start command: `uv run fcc-server`
# 5. Add environment variables
# 6. Deploy!

# Option 3: Fly.io
fly launch --repo sjbrenchley89/free-claude-code
fly deploy
```

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/sjbrenchley89/free-claude-code/issues
- Railway Docs: https://railway.app/docs
- Render Docs: https://render.com/docs
- Fly.io Docs: https://fly.io/docs
