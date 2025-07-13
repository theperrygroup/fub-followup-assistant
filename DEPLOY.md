# 🚀 Deploy FUB Follow-up Assistant to Production

Your FUB Follow-up Assistant is ready to go live! Choose your deployment method below.

## ⚡ Super Quick Deploy (5 minutes)

**Option 1: One-Command Setup**
```bash
# Run this single command to set up and deploy everything
./scripts/setup-production.sh && ./scripts/quick-deploy.sh
```

**Option 2: Step-by-Step**
```bash
# 1. Setup production environment  
./scripts/setup-production.sh

# 2. Edit your API keys
nano .env.production

# 3. Deploy
./scripts/quick-deploy.sh
```

## 🏗️ Deployment Platforms

### 🚂 Railway (Recommended - Easiest)
**Time**: 15 minutes | **Cost**: $5-20/month | **Skill Level**: Beginner

✅ **Why Railway?**
- Automatic deployments from GitHub
- Built-in PostgreSQL and Redis
- Free SSL certificates
- Simple environment variable management
- Excellent for MVPs and small to medium apps

📋 **Steps:**
1. Run `./scripts/quick-deploy.sh` and choose option 1
2. Or follow: [Railway Deploy Guide](deploy/railway-deploy.md)

### 🎨 Render
**Time**: 20 minutes | **Cost**: $7-25/month | **Skill Level**: Beginner

✅ **Why Render?**
- Free tier available
- Automatic deploys from GitHub  
- Built-in databases
- Good for startups

📋 **Steps:**
1. Push code to GitHub
2. Go to [render.com](https://render.com)
3. Create services: API, Marketing, Embed UI
4. Add PostgreSQL and Redis
5. Configure environment variables

### 🌊 DigitalOcean App Platform
**Time**: 25 minutes | **Cost**: $12-50/month | **Skill Level**: Intermediate

✅ **Why DigitalOcean?**
- Predictable pricing
- Good performance
- Managed databases
- Great for scaling

📋 **Steps:**
1. Go to [DigitalOcean Apps](https://cloud.digitalocean.com/apps)
2. Create app from GitHub repo
3. Configure components and databases
4. Set environment variables

### ☁️ AWS (Advanced)
**Time**: 1-2 hours | **Cost**: $20-100/month | **Skill Level**: Advanced

✅ **Why AWS?**
- Maximum scalability
- Enterprise features
- Global CDN
- Complete control

📋 **Steps:**
1. Use AWS CDK or ECS with Fargate
2. Set up RDS (PostgreSQL) and ElastiCache (Redis)
3. Configure Application Load Balancer
4. Set up CloudFront CDN

## 🔧 Required API Keys

Before deploying, you need these accounts and API keys:

### 1. OpenAI
- **Get from**: https://platform.openai.com/api-keys
- **Cost**: ~$0.002 per 1K tokens (very cheap)
- **Usage**: AI chat responses

### 2. Stripe
- **Get from**: https://dashboard.stripe.com/apikeys
- **Cost**: 2.9% + 30¢ per transaction
- **Usage**: Subscription billing

### 3. Follow Up Boss
- **Get from**: FUB Admin → Apps & Integrations
- **Cost**: Free (part of your FUB subscription)
- **Usage**: CRM integration

## 🌐 Domain Setup

### Option A: Use Platform Domains (Free)
- Railway: `your-app.up.railway.app`
- Render: `your-app.onrender.com`
- DigitalOcean: `your-app.digitaloceanspaces.com`

### Option B: Custom Domain ($10-15/year)
1. Buy domain from Namecheap, Google Domains, etc.
2. Point DNS to your platform
3. Platform will handle SSL automatically

## 📋 Post-Deployment Checklist

After deployment, complete these steps:

### ✅ 1. Test Your Apps
```bash
# Test API
curl https://your-api-domain.com/health

# Test marketing site  
open https://your-domain.com

# Test embed UI
open https://your-app-domain.com
```

### ✅ 2. Configure Stripe Webhooks
1. Go to Stripe Dashboard → Webhooks
2. Add endpoint: `https://your-api-domain.com/webhooks/stripe`
3. Subscribe to these events:
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`

### ✅ 3. Set Up Follow Up Boss Integration
1. Go to FUB Admin → Apps & Integrations
2. Create new app:
   - **Name**: FUB Follow-up Assistant
   - **iframe URL**: `https://your-app-domain.com`
   - **Webhook URL**: `https://your-api-domain.com/webhooks/fub`
3. Copy Client ID and Secret to your environment variables

### ✅ 4. Test End-to-End
1. Open a lead in Follow Up Boss
2. Look for your app iframe in the sidebar
3. Test authentication and chat functionality
4. Test note creation

## 💰 Cost Breakdown

### Monthly Costs (Estimated)
- **Hosting**: $5-50/month (depending on platform)
- **Database**: $0-25/month (often included)
- **Domain**: $1-2/month
- **OpenAI API**: $1-10/month (based on usage)
- **Stripe fees**: 2.9% of revenue

### Total: $10-100/month
Most startups will be in the $15-30/month range.

## 🆘 Need Help?

### Common Issues
1. **Build failing**: Check Node.js version (needs 18+)
2. **API not connecting**: Verify DATABASE_URL and REDIS_URL
3. **FUB iframe not loading**: Check CORS settings and domain
4. **Stripe webhooks failing**: Verify webhook secret

### Get Support
- 📖 Check the [README.md](README.md) for detailed docs
- 🐛 Open GitHub issue for bugs
- 💬 Email: your-support-email@domain.com

## 🎉 You're Live!

Once deployed, your FUB Follow-up Assistant will:
- ✅ Provide AI-powered follow-up suggestions
- ✅ Create notes directly in Follow Up Boss
- ✅ Handle subscriptions and billing automatically
- ✅ Scale to handle thousands of users

**Congratulations on launching your SaaS! 🚀** 