# FUB Follow-up Assistant - Deployment Checklist

## 🔑 Phase 1: API Keys & Accounts (15 minutes)

### OpenAI Setup
- [ ] Get OpenAI API key from https://platform.openai.com/api-keys
- [ ] Add billing information to OpenAI account
- [ ] Test API key with a simple request

### Stripe Setup  
- [ ] Create Stripe account at https://dashboard.stripe.com/register
- [ ] Get API keys (Publishable + Secret)
- [ ] Create products:
  - [ ] Starter: $29/month (100 conversations)
  - [ ] Professional: $59/month (500 conversations) 
  - [ ] Enterprise: $99/month (unlimited)

### Follow Up Boss Setup
- [ ] Access FUB admin panel
- [ ] Go to Apps & Integrations
- [ ] Create new app with iframe integration
- [ ] Get Client ID and Client Secret
- [ ] Configure webhook URL (will set later)

## 🏗️ Phase 2: Choose Deployment Platform (30 minutes)

### Option A: DigitalOcean (Recommended for simplicity)
- [ ] Create DigitalOcean account
- [ ] Set up App Platform deployment
- [ ] Configure environment variables
- [ ] Set up managed database (PostgreSQL + Redis)

### Option B: AWS (More complex but scalable)
- [ ] Create AWS account
- [ ] Set up ECS/Fargate containers
- [ ] Configure RDS (PostgreSQL) and ElastiCache (Redis)
- [ ] Set up Application Load Balancer
- [ ] Configure Route 53 for domain

### Option C: Railway/Render/Fly.io (Easiest)
- [ ] Create account on chosen platform
- [ ] Connect GitHub repository
- [ ] Configure auto-deployment
- [ ] Add managed database add-ons

## 🌐 Phase 3: Domain & SSL (15 minutes)

- [ ] Purchase domain (e.g., fub-assistant.com)
- [ ] Configure DNS to point to deployment
- [ ] Enable SSL/HTTPS (usually automatic)
- [ ] Test domain access

## 🔗 Phase 4: Configure Integrations (30 minutes)

### Stripe Webhooks
- [ ] Add webhook endpoint: https://yourdomain.com/webhooks/stripe
- [ ] Subscribe to events:
  - customer.subscription.created
  - customer.subscription.updated  
  - customer.subscription.deleted
  - invoice.payment_succeeded
  - invoice.payment_failed
- [ ] Get webhook signing secret

### Follow Up Boss App
- [ ] Update iframe URL to: https://yourdomain.com
- [ ] Set webhook URL to: https://yourdomain.com/webhooks/fub
- [ ] Test iframe integration
- [ ] Configure HMAC secret

## ✅ Phase 5: Final Testing (45 minutes)

- [ ] Test marketing site loads
- [ ] Test iframe authentication
- [ ] Test AI chat functionality  
- [ ] Test note creation in FUB
- [ ] Test Stripe subscription flow
- [ ] Test webhook endpoints
- [ ] Load testing with multiple users

## 📊 Phase 6: Monitoring & Analytics (30 minutes)

- [ ] Set up application monitoring
- [ ] Configure error tracking
- [ ] Set up uptime monitoring
- [ ] Add Google Analytics
- [ ] Configure log aggregation

## 📈 Phase 7: Go Live & Scale

- [ ] Announce to beta users
- [ ] Monitor performance and errors
- [ ] Scale resources as needed
- [ ] Iterate based on user feedback

---

**Total Time Estimate: 3-4 hours**
**Cost Estimate: $50-100/month for hosting + API usage** 