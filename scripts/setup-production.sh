#!/bin/bash

# FUB Follow-up Assistant - Production Setup Script
# This script helps you configure all the necessary services for production

set -e

echo "🚀 FUB Follow-up Assistant - Production Setup"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v node &> /dev/null; then
    print_error "Node.js is required but not installed."
    exit 1
fi

if ! command -v pnpm &> /dev/null; then
    print_warning "pnpm not found. Installing..."
    npm install -g pnpm
fi

if ! command -v git &> /dev/null; then
    print_error "Git is required but not installed."
    exit 1
fi

print_step "Prerequisites check passed"

# Build all packages
echo ""
echo "Building all packages..."

pnpm install --frozen-lockfile
print_step "Dependencies installed"

cd packages/shared && pnpm build
print_step "Shared package built"

cd ../../apps/embed-ui && pnpm build  
print_step "Embed UI built"

cd ../marketing && pnpm build
print_step "Marketing site built"

cd ../../

# Generate secrets
echo ""
echo "Generating security secrets..."

SECRET_KEY=$(openssl rand -hex 32)
NEXTAUTH_SECRET=$(openssl rand -hex 32)

print_step "Security secrets generated"

# Create production environment template
echo ""
echo "Creating production environment template..."

cat > .env.production << EOF
# =============================================================================
# FUB Follow-up Assistant - Production Environment
# Generated on $(date)
# =============================================================================

# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=sk-proj-REPLACE_WITH_YOUR_OPENAI_KEY

# Stripe Configuration (REQUIRED)
STRIPE_SECRET_KEY=sk_live_REPLACE_WITH_YOUR_STRIPE_SECRET
STRIPE_PUBLISHABLE_KEY=pk_live_REPLACE_WITH_YOUR_STRIPE_PUBLISHABLE  
STRIPE_WEBHOOK_SECRET=whsec_REPLACE_WITH_YOUR_WEBHOOK_SECRET

# Follow Up Boss Configuration (REQUIRED)
FUB_CLIENT_ID=REPLACE_WITH_YOUR_FUB_CLIENT_ID
FUB_CLIENT_SECRET=REPLACE_WITH_YOUR_FUB_CLIENT_SECRET
FUB_WEBHOOK_SECRET=REPLACE_WITH_YOUR_FUB_WEBHOOK_SECRET

# Database URLs (Will be provided by hosting platform)
DATABASE_URL=postgresql://username:password@host:port/database
REDIS_URL=redis://username:password@host:port

# Application Configuration
APP_ENV=production
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

# Security Configuration (AUTO-GENERATED)
SECRET_KEY=${SECRET_KEY}
NEXTAUTH_SECRET=${NEXTAUTH_SECRET}

# Domain Configuration (REPLACE WITH YOUR DOMAINS)
API_BASE_URL=https://api.yourdomain.com
NEXTAUTH_URL=https://yourdomain.com
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
EOF

print_step "Production environment template created (.env.production)"

# Git repository setup
echo ""
echo "Setting up Git repository..."

if [ ! -d ".git" ]; then
    git init
    print_step "Git repository initialized"
else
    print_step "Git repository already exists"
fi

# Create .gitignore if it doesn't exist
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << EOF
# Environment files
.env
.env.local
.env.production
.env.*.local

# Dependencies
node_modules/
__pycache__/
*.pyc

# Build outputs
dist/
build/
.next/

# Logs
*.log
logs/

# Database
*.db
*.sqlite

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Docker
docker-compose.override.yml
EOF
    print_step ".gitignore created"
fi

# Add all files to git
git add .
if git diff --staged --quiet; then
    print_step "No changes to commit"
else
    git commit -m "Initial commit - FUB Follow-up Assistant ready for production"
    print_step "Files committed to git"
fi

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Next steps:"
echo "1. 📝 Edit .env.production with your actual API keys"
echo "2. 🚀 Deploy to your chosen platform:"
echo "   • Railway: https://railway.app (Recommended - easiest)"
echo "   • Render: https://render.com"  
echo "   • DigitalOcean: https://digitalocean.com"
echo "3. 🌐 Configure your domain and SSL"
echo "4. 🔗 Set up Follow Up Boss iframe integration"
echo "5. 💳 Configure Stripe webhooks"
echo ""
echo "📋 See deployment-checklist.md for detailed steps"
echo "🚂 See deploy/railway-deploy.md for Railway deployment"
echo ""

# Check if we should open browser tabs
read -p "Open setup links in browser? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Opening setup pages..."
    open "https://platform.openai.com/api-keys" 2>/dev/null || true
    open "https://dashboard.stripe.com/apikeys" 2>/dev/null || true  
    open "https://railway.app" 2>/dev/null || true
    print_step "Setup pages opened in browser"
fi

echo ""
print_step "Production setup complete! 🚀" 