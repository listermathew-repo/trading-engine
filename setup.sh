#!/bin/bash

echo "================================"
echo "TradingView Webhook Setup Script"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js 18+${NC}"
    echo "Visit: https://nodejs.org/"
    exit 1
fi

echo -e "${GREEN}✓ Node.js found${NC} ($(node -v))"
echo ""

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ npm found${NC} ($(npm -v))"
echo ""

# Step 1: Install dependencies
echo -e "${BLUE}[1/4] Installing dependencies...${NC}"
npm install

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Dependencies installed${NC}"
echo ""

# Step 2: Generate Prisma client
echo -e "${BLUE}[2/4] Generating Prisma client...${NC}"
npx prisma generate

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to generate Prisma client${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Prisma client generated${NC}"
echo ""

# Step 3: Run migrations
echo -e "${BLUE}[3/4] Running database migrations...${NC}"
npx prisma migrate dev --name init

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Failed to run migrations${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Database initialized${NC}"
echo ""

# Step 4: Summary
echo -e "${BLUE}[4/4] Setup complete!${NC}"
echo ""
echo "================================"
echo "✨ Setup Completed Successfully!"
echo "================================"
echo ""
echo "Next steps:"
echo ""
echo -e "${GREEN}1. Start the development server:${NC}"
echo "   npm run dev"
echo ""
echo -e "${GREEN}2. Open in your browser:${NC}"
echo "   http://localhost:3000"
echo ""
echo -e "${GREEN}3. Test the webhook:${NC}"
echo "   Use the 'Test Webhook' panel on the dashboard"
echo ""
echo -e "${GREEN}4. Read the documentation:${NC}"
echo "   - README_WEBHOOK.md (Overview)"
echo "   - WEBHOOK_INTEGRATION.md (API Details)"
echo "   - TESTING_GUIDE.md (Testing Methods)"
echo ""
echo "================================"
