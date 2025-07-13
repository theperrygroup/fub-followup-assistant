# Deploy to Railway (Easiest - 15 minutes)

Railway is the fastest way to get your app live with minimal configuration.

## 🚀 Step 1: Prepare Repository

```bash
# Initialize git if not already done
git init
git add .
git commit -m "Initial commit - FUB Follow-up Assistant"

# Push to GitHub
gh repo create fub-followup-assistant --public
git remote add origin https://github.com/yourusername/fub-followup-assistant.git
git push -u origin main
```

## 🚂 Step 2: Deploy to Railway

1. **Sign up**: Go to https://railway.app and sign up with GitHub
2. **New Project**: Click "New Project" → "Deploy from GitHub repo"
3. **Select Repo**: Choose your `fub-followup-assistant` repository
4. **Configure Services**: Railway will auto-detect your services

### Add Environment Variables

In Railway dashboard, go to each service and add these variables:

#### API Service
```env
OPENAI_API_KEY=sk-your-openai-key
STRIPE_SECRET_KEY=sk_your-stripe-secret
STRIPE_WEBHOOK_SECRET=whsec_your-webhook-secret
FUB_CLIENT_ID=your-fub-client-id
FUB_CLIENT_SECRET=your-fub-client-secret
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
APP_ENV=production
```

#### Marketing Service
```env
API_BASE_URL=https://api-production-xxxx.up.railway.app
STRIPE_PUBLISHABLE_KEY=pk_your-stripe-publishable
NEXTAUTH_URL=https://marketing-production-xxxx.up.railway.app
NEXTAUTH_SECRET=your-random-secret-here
```

## 🗄️ Step 3: Add Databases

1. **PostgreSQL**: Click "+ New" → "Database" → "PostgreSQL"
2. **Redis**: Click "+ New" → "Database" → "Redis"
3. Railway will auto-generate connection URLs

## 🌐 Step 4: Configure Domains

1. Go to each service → "Settings" → "Domains"
2. Generate Railway domains or add custom domains:
   - API: `api.yourdomain.com`
   - Marketing: `yourdomain.com` 
   - Embed UI: `app.yourdomain.com`

## ✅ Step 5: Deploy & Test

Railway will automatically deploy. Check logs in dashboard and test:

```bash
# Test API health
curl https://your-api-domain.railway.app/health

# Test marketing site
open https://your-marketing-domain.railway.app
```

**Total time: 15 minutes**
**Cost: ~$5-20/month** 