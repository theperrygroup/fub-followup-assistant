# FUB Follow-up Assistant

AI-powered follow-up suggestions and automated note creation for Follow Up Boss CRM.

## 🚀 Features

- **AI-Powered Suggestions**: Get personalized follow-up recommendations based on lead data
- **Automatic Note Creation**: One-click note creation directly in Follow Up Boss
- **Secure Integration**: HMAC-verified iframe integration with Follow Up Boss
- **Rate Limiting**: Account and IP-based rate limiting for cost control
- **Subscription Management**: Stripe-powered billing and subscription handling
- **Real Estate Expertise**: AI trained on real estate best practices

## 🏗️ Architecture

- **Backend**: FastAPI with PostgreSQL and Redis
- **Frontend**: React (iframe embed) + Next.js (marketing site)
- **AI**: OpenAI GPT-4o-mini with real estate prompts
- **Billing**: Stripe for subscription management
- **Deployment**: Docker containers with nginx

## 📋 Prerequisites

Before getting started, you'll need:

1. **OpenAI API Key** - [Get one here](https://platform.openai.com/api-keys)
2. **Stripe Account** - [Sign up here](https://dashboard.stripe.com/register)
3. **Follow Up Boss App** - Create an app in your FUB admin panel
4. **Docker & Docker Compose** - [Install here](https://docs.docker.com/get-docker/)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <your-repo>
cd fub_gpt_super_3

# Copy environment template
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` and add your API keys:

```bash
# Required
OPENAI_API_KEY=sk-your-openai-api-key-here
STRIPE_SECRET_KEY=sk_test_your-stripe-secret-key-here
STRIPE_PUBLISHABLE_KEY=pk_test_your-stripe-publishable-key-here
FUB_CLIENT_ID=your-fub-client-id-here
FUB_CLIENT_SECRET=your-fub-client-secret-here
```

### 3. Start the Application

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Access the Applications

- **Marketing Site**: http://localhost:3001
- **Embed UI**: http://localhost:5173
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🔧 Development Setup

For local development without Docker:

### Backend (FastAPI)

```bash
cd apps/api

# Install dependencies
pip install -r requirements.txt

# Start database (or use Docker)
docker-compose up postgres redis -d

# Run FastAPI
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend (React Embed UI)

```bash
cd apps/embed-ui

# Install dependencies
pnpm install

# Start development server
pnpm dev
```

### Marketing Site (Next.js)

```bash
cd apps/marketing

# Install dependencies
pnpm install

# Start development server
pnpm dev
```

## 📦 Project Structure

```
├── apps/
│   ├── api/              # FastAPI backend
│   │   ├── routes/       # API routes
│   │   ├── services/     # Business logic
│   │   ├── models.py     # Database models
│   │   └── main.py       # FastAPI app
│   ├── embed-ui/         # React iframe app
│   │   └── src/
│   │       └── components/
│   └── marketing/        # Next.js marketing site
│       └── src/
├── packages/
│   └── shared/           # Shared TypeScript types
├── infra/
│   └── postgres/         # Database initialization
├── docker-compose.yml    # Docker services
└── package.json          # Workspace config
```

## 🔌 Follow Up Boss Integration

### 1. Create FUB App

1. Go to your Follow Up Boss admin panel
2. Navigate to Apps & Integrations
3. Create a new app with these settings:
   - **Name**: FUB Follow-up Assistant
   - **iframe URL**: `http://localhost:5173` (dev) or your domain
   - **Webhook URL**: `http://localhost:8000/webhooks/fub` (dev) or your domain

### 2. Configure HMAC

The app uses HMAC verification for security. Get your webhook secret from FUB and add it to your `.env`:

```bash
FUB_WEBHOOK_SECRET=your-webhook-secret-here
```

### 3. Test Integration

1. Open a lead in Follow Up Boss
2. Look for the "FUB Assistant" iframe in the sidebar
3. The app should authenticate automatically and show the chat interface

## 💳 Stripe Configuration

### 1. Create Stripe Products

Create these products in your Stripe dashboard:

- **Starter**: $29/month - 100 conversations
- **Professional**: $59/month - 500 conversations  
- **Enterprise**: $99/month - Unlimited conversations

### 2. Configure Webhooks

Add a webhook endpoint in Stripe pointing to:
`https://your-domain.com/webhooks/stripe`

Subscribe to these events:
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

## 🛡️ Security Features

- **HMAC Verification**: All FUB iframe requests verified with HMAC
- **JWT Authentication**: Secure token-based auth between services
- **Rate Limiting**: 10 requests/minute per account, 100/minute per IP
- **Input Validation**: Pydantic models validate all inputs
- **SQL Injection Protection**: SQLModel with parameterized queries

## 📊 Monitoring & Logging

- **Health Checks**: All services have health check endpoints
- **Structured Logging**: JSON logs in production with request tracing
- **Rate Limit Tracking**: Redis-based sliding window rate limiting
- **Error Tracking**: Comprehensive error handling and reporting

## 🚀 Deployment

### Production Environment

1. **Update Environment Variables**:
   ```bash
   APP_ENV=production
   DATABASE_URL=postgresql://user:pass@your-db-host:5432/dbname
   REDIS_URL=redis://your-redis-host:6379/0
   ALLOWED_ORIGINS=https://your-domain.com
   ```

2. **SSL Configuration**:
   - Add nginx proxy with SSL termination
   - Update FUB app iframe URL to use HTTPS
   - Configure Stripe webhook URL with HTTPS

3. **Database Migration**:
   ```bash
   # Run migrations on production database
   docker-compose exec api python -c "from sqlmodel import SQLModel, create_engine; from config import settings; engine = create_engine(settings.database_url); SQLModel.metadata.create_all(engine)"
   ```

### Scaling Considerations

- **Database**: Use managed PostgreSQL (AWS RDS, GCP Cloud SQL)
- **Cache**: Use managed Redis (AWS ElastiCache, Redis Cloud)
- **Load Balancing**: Multiple API instances behind load balancer
- **Container Orchestration**: Kubernetes or AWS ECS for auto-scaling

## 🧪 Testing

```bash
# Run backend tests
cd apps/api
pytest

# Run frontend tests
cd apps/embed-ui
npm test

# Run integration tests
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

## 📝 API Documentation

Visit http://localhost:8000/docs for interactive API documentation (Swagger UI).

Key endpoints:
- `POST /auth/iframe-login` - Authenticate iframe requests
- `POST /chat` - Send chat messages to AI
- `POST /fub/notes` - Create notes in Follow Up Boss
- `POST /webhooks/stripe` - Handle Stripe events

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check this README and API docs
- **Issues**: Create a GitHub issue for bugs or feature requests
- **Email**: support@your-domain.com for general inquiries

## 🎯 Roadmap

- [ ] Advanced AI training with custom real estate data
- [ ] Multi-language support
- [ ] Mobile app for on-the-go access
- [ ] Advanced analytics and reporting
- [ ] Integration with more CRM systems
- [ ] White-label options for brokerages 