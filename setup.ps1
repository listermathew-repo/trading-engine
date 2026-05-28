Write-Host "================================" -ForegroundColor Cyan
Write-Host "TradingView Webhook Setup Script" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if Node.js is installed
$nodeVersion = node -v 2>$null
if ($null -eq $nodeVersion) {
    Write-Host "❌ Node.js is not installed. Please install Node.js 18+" -ForegroundColor Red
    Write-Host "Visit: https://nodejs.org/" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Node.js found ($nodeVersion)" -ForegroundColor Green
Write-Host ""

# Check if npm is installed
$npmVersion = npm -v 2>$null
if ($null -eq $npmVersion) {
    Write-Host "❌ npm is not installed" -ForegroundColor Red
    exit 1
}

Write-Host "✓ npm found ($npmVersion)" -ForegroundColor Green
Write-Host ""

# Step 1: Install dependencies
Write-Host "[1/4] Installing dependencies..." -ForegroundColor Blue
npm install

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Step 2: Generate Prisma client
Write-Host "[2/4] Generating Prisma client..." -ForegroundColor Blue
npx prisma generate

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to generate Prisma client" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Prisma client generated" -ForegroundColor Green
Write-Host ""

# Step 3: Run migrations
Write-Host "[3/4] Running database migrations..." -ForegroundColor Blue
npx prisma migrate dev --name init

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Failed to run migrations" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Database initialized" -ForegroundColor Green
Write-Host ""

# Step 4: Summary
Write-Host "[4/4] Setup complete!" -ForegroundColor Blue
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "✨ Setup Completed Successfully!" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host ""
Write-Host "1. Start the development server:" -ForegroundColor Green
Write-Host "   npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "2. Open in your browser:" -ForegroundColor Green
Write-Host "   http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "3. Test the webhook:" -ForegroundColor Green
Write-Host "   Use the 'Test Webhook' panel on the dashboard" -ForegroundColor White
Write-Host ""
Write-Host "4. Read the documentation:" -ForegroundColor Green
Write-Host "   - README_WEBHOOK.md (Overview)" -ForegroundColor White
Write-Host "   - WEBHOOK_INTEGRATION.md (API Details)" -ForegroundColor White
Write-Host "   - TESTING_GUIDE.md (Testing Methods)" -ForegroundColor White
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
