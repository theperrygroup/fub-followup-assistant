#!/bin/bash

# FUB Follow-up Assistant - One-Command Deploy
# This script deploys your app in under 5 minutes

set -e

echo "⚡ FUB Follow-up Assistant - Quick Deploy"
echo "========================================"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_step() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    echo "❌ .env.production not found!"
    echo "Run: ./scripts/setup-production.sh first"
    exit 1
fi

# Check if git repo exists and has commits
if [ ! -d ".git" ] || [ -z "$(git log --oneline 2>/dev/null)" ]; then
    echo "❌ Git repository not found or empty!"
    echo "Run: ./scripts/setup-production.sh first"
    exit 1
fi

print_step "Prerequisites check passed"

# Ask for deployment platform
echo ""
echo "Choose deployment platform:"
echo "1) Railway (Recommended - easiest)"
echo "2) Render"
echo "3) DigitalOcean App Platform"
echo "4) Manual Docker deployment"
echo ""
read -p "Enter choice (1-4): " -n 1 -r platform
echo ""

case $platform in
    1)
        echo "🚂 Deploying to Railway..."
        
        # Check if Railway CLI is installed
        if ! command -v railway &> /dev/null; then
            print_info "Installing Railway CLI..."
            npm install -g @railway/cli
        fi
        
        # Login to Railway
        print_info "Please login to Railway in the browser window that opens..."
        railway login
        
        # Create new project
        railway new fub-followup-assistant
        cd fub-followup-assistant
        
        # Add services
        railway service create api
        railway service create marketing  
        railway service create embed-ui
        
        # Add databases
        railway add postgresql
        railway add redis
        
        print_step "Railway project created"
        
        # Deploy
        railway up --service api
        railway up --service marketing
        railway up --service embed-ui
        
        print_step "Deployed to Railway!"
        echo ""
        echo "🎉 Your app is live!"
        echo "📱 Marketing site: Check Railway dashboard for URL"
        echo "🔧 Next: Configure environment variables in Railway dashboard"
        ;;
        
    2)
        echo "🎨 Deploying to Render..."
        echo "Please follow these steps:"
        echo "1. Go to https://render.com"
        echo "2. Connect your GitHub repository"
        echo "3. Create 3 services: api, marketing, embed-ui"
        echo "4. Add PostgreSQL and Redis databases"
        echo "5. Configure environment variables from .env.production"
        ;;
        
    3)
        echo "🌊 Deploying to DigitalOcean..."
        echo "Please follow these steps:"
        echo "1. Go to https://cloud.digitalocean.com/apps"
        echo "2. Create App from GitHub repository"
        echo "3. Configure 3 components: api, marketing, embed-ui"
        echo "4. Add managed databases: PostgreSQL + Redis"
        echo "5. Configure environment variables from .env.production"
        ;;
        
    4)
        echo "🐳 Manual Docker deployment..."
        echo "Building Docker images..."
        
        docker build -t fub-api ./apps/api
        docker build -t fub-embed-ui ./apps/embed-ui  
        docker build -t fub-marketing ./apps/marketing
        
        print_step "Docker images built"
        echo ""
        echo "To deploy:"
        echo "1. Push images to your registry"
        echo "2. Set up PostgreSQL and Redis"
        echo "3. Run: docker-compose up -d"
        echo "4. Configure environment variables"
        ;;
        
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "📋 Post-deployment checklist:"
echo "1. ✅ Configure environment variables"
echo "2. ✅ Test API health endpoint"
echo "3. ✅ Set up Stripe webhooks"
echo "4. ✅ Configure Follow Up Boss iframe"
echo "5. ✅ Test end-to-end functionality"
echo ""
echo "See deployment-checklist.md for detailed steps!" 