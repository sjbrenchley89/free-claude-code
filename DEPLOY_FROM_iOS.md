# Deploy free-claude-code from iPhone/iPad

Simple guide to deploy and manage your AI proxy server entirely from mobile.

## 5-Minute Setup

### Step 1: Create Railway Account (Free)
1. Open Safari on iPhone
2. Go to [railway.app](https://railway.app)
3. Tap "Sign Up" → "Continue with GitHub"
4. Log in to GitHub → Authorize Railway

### Step 2: Deploy Your Server
1. In Railway, tap "Start a new Project"
2. Select "Deploy from GitHub Repo"
3. Search for `sjbrenchley89/free-claude-code`
4. Tap to select it
5. Scroll down → Add Environment Variables:
   - **Key**: `ANTHROPIC_API_KEY`
   - **Value**: Your API key from https://console.anthropic.com/account/keys
6. Tap "Deploy"
7. Wait 2-3 minutes ⏳

### Step 3: Get Your Server URL
1. In Railway dashboard, tap your deployment
2. Tap "Settings" → "Domains"
3. Copy your domain (looks like: `free-claude-code-prod.railway.app`)
4. Test it: Open Safari → `https://your-domain.railway.app/health`
5. Should see: `{"status": "healthy"}`

### Step 4: Access Admin Dashboard
1. Open: `https://your-domain.railway.app/admin`
2. You can now:
   - View API status
   - Monitor requests
   - Check available models
   - Configure providers
   - View real-time logs

## What You Get

✅ **AI Proxy Server**: Access 30+ AI models
✅ **OpenAI Compatible API**: `/v1/messages`, `/v1/responses`
✅ **Admin Dashboard**: Monitor and manage from browser
✅ **Authentication**: Optional token-based auth
✅ **Monitoring**: Real-time metrics and logs

## After Deployment

### Test Your API

```bash
# From iPhone's Notes, paste this URL:
https://your-domain.railway.app/health

# Then use curl or API client to test:
https://your-domain.railway.app/v1/models
```

### Use with Coding Tools

Configure these to use your deployed server:

**Claude Code CLI**:
```bash
export ANTHROPIC_API_BASE_URL=https://your-domain.railway.app
```

**Cursor / VS Code**:
- Extensions → Anthropic Claude
- Settings → API Base URL → `https://your-domain.railway.app`

**Cline / VSCode Extension**:
- Settings → API Provider → Custom
- Base URL → `https://your-domain.railway.app`

## Mobile Development Workflow

### To Deploy Code Changes from iPhone:

1. **Install Git Client**
   - App Store → Search "Working Copy" or "GitDown"
   - Free options: GitDown (basic), Coduo (basic editor)
   - Paid options: Working Copy ($14.99, full-featured)

2. **Edit Code**
   - Clone: `https://github.com/sjbrenchley89/free-claude-code.git`
   - Edit files in app
   - Commit & push changes

3. **GitHub Actions Deploys**
   - Railroad auto-detects GitHub commits
   - Automatically redeploys within 30 seconds
   - No additional action needed

4. **Check Logs**
   - Railway → Your Project → Logs tab
   - Real-time output from server
   - Scroll to see latest events

## Common Tasks

### View Server Logs
```
Railway Dashboard → Your Project → Logs tab
```

### Restart Server
```
Railway Dashboard → Deployments → Redeploy
```

### Update API Key
```
Railway Dashboard → Variables → Edit ANTHROPIC_API_KEY
```

### Add New Provider
1. Go to: `https://your-domain.railway.app/admin`
2. Settings → Providers
3. Add new API key
4. Select as default or use in requests

### Monitor Performance
```
Railway Dashboard → Metrics tab
- CPU usage
- Memory usage  
- Request count
- Response times
```

## Pricing

| Item | Cost |
|------|------|
| Railway Server (starter) | $5/month |
| Anthropic API | Based on usage (2-8 cents per 1M tokens) |
| GitHub hosting | Free |
| **Total** | **~$10-15/month** |

Free tier available for testing (limited resources).

## Troubleshooting

### "Deploy failed"
- Check Railway logs for specific error
- Verify ANTHROPIC_API_KEY is set correctly
- Ensure git repository is public

### "Health check fails"
- Wait 30 seconds after deploy
- Check ANTHROPIC_API_KEY in Railway Variables
- Verify API key is valid from console.anthropic.com

### "Admin dashboard shows error"
- Refresh page (pull down to refresh)
- Check browser console (Safari → Develop → Console)
- Verify server URL is correct

### "API calls are slow"
- Normal during first request (cold start takes 5-10s)
- Subsequent requests are < 100ms
- Check Railway metrics for actual server performance

## Alternative Platforms

If Railway isn't available in your region:

### Render
- Similar to Railway
- Go to [render.com](https://render.com)
- $7/month starter tier
- Same deployment flow

### Fly.io
- Global deployment
- Free tier available
- Requires `fly` CLI (harder on mobile)
- Better for experienced developers

## Quick Links

| Resource | URL |
|----------|-----|
| Railway | https://railway.app |
| Anthropic API Keys | https://console.anthropic.com/account/keys |
| GitHub Repository | https://github.com/sjbrenchley89/free-claude-code |
| Admin Dashboard | `https://your-domain.railway.app/admin` |
| Health Check | `https://your-domain.railway.app/health` |
| API Models | `https://your-domain.railway.app/v1/models` |

## Support

- **GitHub Issues**: https://github.com/sjbrenchley89/free-claude-code/issues
- **Railway Help**: https://railway.app/support
- **Anthropic Docs**: https://docs.anthropic.com

---

**Deployed successfully!** 🎉

Your AI proxy server is now running and accessible from any device with a browser. Enjoy!
