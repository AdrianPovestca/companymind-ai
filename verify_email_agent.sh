#!/bin/bash

echo "════════════════════════════════════════════════════════════"
echo "🔍 EMAIL AGENT v1.0 — COMPLETE VERIFICATION"
echo "════════════════════════════════════════════════════════════"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counter
TOTAL=0
PASSED=0

# Function to check item
check() {
    TOTAL=$((TOTAL + 1))
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}❌ $2${NC}"
    fi
}

echo ""
echo "📦 CHECKING CORE FILES..."
echo "────────────────────────────────────────────────────────────"

# Check core files exist
[ -f "src/email_parser.py" ] && echo -e "${GREEN}✅ Parser${NC}" || echo -e "${RED}❌ Parser${NC}"
[ -f "src/email_analyzer.py" ] && echo -e "${GREEN}✅ Analyzer${NC}" || echo -e "${RED}❌ Analyzer${NC}"
[ -f "src/email_decision.py" ] && echo -e "${GREEN}✅ Decision${NC}" || echo -e "${RED}❌ Decision${NC}"
[ -f "src/email_responder.py" ] && echo -e "${GREEN}✅ Responder (old)${NC}" || echo -e "${RED}❌ Responder${NC}"
[ -f "src/email_smart_responder.py" ] && echo -e "${GREEN}✅ Smart Responder (new)${NC}" || echo -e "${RED}❌ Smart Responder${NC}"
[ -f "src/email_database.py" ] && echo -e "${GREEN}✅ Database${NC}" || echo -e "${RED}❌ Database${NC}"
[ -f "src/email_thread.py" ] && echo -e "${GREEN}✅ Thread${NC}" || echo -e "${RED}❌ Thread${NC}"
[ -f "src/email_agent.py" ] && echo -e "${GREEN}✅ Agent${NC}" || echo -e "${RED}❌ Agent${NC}"

echo ""
echo "🔌 CHECKING CONNECTORS..."
echo "────────────────────────────────────────────────────────────"

[ -f "src/email_connector.py" ] && echo -e "${GREEN}✅ Base Connector${NC}" || echo -e "${RED}❌ Base Connector${NC}"
[ -f "src/email_provider_registry.py" ] && echo -e "${GREEN}✅ Provider Registry${NC}" || echo -e "${RED}❌ Provider Registry${NC}"
[ -f "src/gmail_email_connector.py" ] && echo -e "${GREEN}✅ Gmail Connector${NC}" || echo -e "${RED}❌ Gmail Connector${NC}"
[ -f "src/yahoo_email_connector.py" ] && echo -e "${GREEN}✅ Yahoo Connector${NC}" || echo -e "${RED}❌ Yahoo Connector${NC}"
[ -f "src/outlook_email_connector.py" ] && echo -e "${GREEN}✅ Outlook Connector${NC}" || echo -e "${RED}❌ Outlook Connector${NC}"

echo ""
echo "🏭 CHECKING INFRASTRUCTURE..."
echo "────────────────────────────────────────────────────────────"

[ -f "src/agent_factory.py" ] && echo -e "${GREEN}✅ Agent Factory${NC}" || echo -e "${RED}❌ Agent Factory${NC}"
[ -f "requirements.txt" ] && echo -e "${GREEN}✅ Requirements.txt${NC}" || echo -e "${RED}❌ Requirements.txt${NC}"
[ -f ".env" ] && echo -e "${GREEN}✅ .env Config${NC}" || echo -e "${RED}❌ .env Config${NC}"
[ -f ".env.example" ] && echo -e "${GREEN}✅ .env.example${NC}" || echo -e "${RED}❌ .env.example${NC}"
[ -f ".gitignore" ] && echo -e "${GREEN}✅ .gitignore${NC}" || echo -e "${RED}❌ .gitignore${NC}"

echo ""
echo "🧪 CHECKING TESTS..."
echo "────────────────────────────────────────────────────────────"

TEST_COUNT=$(find tests -name "test_*.py" | wc -l)
echo -e "${GREEN}✅ Found $TEST_COUNT test files${NC}"

echo ""
echo "📊 RUNNING ALL TESTS..."
echo "────────────────────────────────────────────────────────────"

python -m pytest -v --tb=short

echo ""
echo "📈 CODE STATISTICS..."
echo "────────────────────────────────────────────────────────────"

echo "Core engine files:"
wc -l src/email_*.py | tail -1

echo ""
echo "Test files:"
wc -l tests/test_*.py | tail -1

echo ""
echo "Git Status:"
echo "────────────────────────────────────────────────────────────"
git log --oneline -5

echo ""
echo "Uncommitted changes:"
git status --short

echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ VERIFICATION COMPLETE"
echo "════════════════════════════════════════════════════════════"
