#!/bin/bash
# Deployment Verification Script for NagrikSathi
# Run this after deployment to verify everything is working

set +e  # Don't exit on error, we want to run all checks

API_URL="${API_URL:-http://localhost:5000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3000}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

ALL_PASSED=true

echo -e "${CYAN}🔍 NagrikSathi Deployment Verification${NC}"
echo -e "${CYAN}======================================${NC}"
echo ""

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3
    
    echo -n "Testing $name..."
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$response" = "200" ]; then
        if [ -n "$expected" ]; then
            content=$(curl -s "$url" 2>/dev/null)
            if echo "$content" | grep -q "$expected"; then
                echo -e " ${GREEN}✅ PASSED${NC}"
                return 0
            else
                echo -e " ${RED}❌ FAILED (unexpected content)${NC}"
                ALL_PASSED=false
                return 1
            fi
        else
            echo -e " ${GREEN}✅ PASSED${NC}"
            return 0
        fi
    else
        echo -e " ${RED}❌ FAILED (Status: $response)${NC}"
        ALL_PASSED=false
        return 1
    fi
}

# Test Backend Health Endpoints
echo -e "${YELLOW}Backend Health Checks:${NC}"
echo -e "${YELLOW}---------------------${NC}"

test_endpoint "Basic Health" "$API_URL/api/health" "healthy"
test_endpoint "Database Health" "$API_URL/api/health/db" "healthy"
test_endpoint "ML Models Health" "$API_URL/api/health/ml"
test_endpoint "Readiness Probe" "$API_URL/api/health/ready"
test_endpoint "Liveness Probe" "$API_URL/api/health/live"

echo ""

# Test Frontend
echo -e "${YELLOW}Frontend Check:${NC}"
echo -e "${YELLOW}--------------${NC}"

test_endpoint "Frontend Accessible" "$FRONTEND_URL"

echo ""

# Check Docker Containers (if using Docker)
echo -e "${YELLOW}Docker Containers:${NC}"
echo -e "${YELLOW}-----------------${NC}"

if command -v docker-compose &> /dev/null; then
    containers=$(docker-compose ps --services 2>/dev/null)
    if [ -n "$containers" ]; then
        for container in $containers; do
            status=$(docker-compose ps "$container" 2>/dev/null | grep "Up")
            if [ -n "$status" ]; then
                echo -e "  $container : ${GREEN}✅ Running${NC}"
            else
                echo -e "  $container : ${RED}❌ Not Running${NC}"
                ALL_PASSED=false
            fi
        done
    else
        echo -e "  ${YELLOW}Docker Compose not detected or not running${NC}"
    fi
else
    echo -e "  ${YELLOW}Docker Compose not installed${NC}"
fi

echo ""

# Check Required Files
echo -e "${YELLOW}Required Files:${NC}"
echo -e "${YELLOW}--------------${NC}"

required_files=(
    "backend/ml_models/classifier.pkl"
    "backend/ml_models/vectorizer.pkl"
    ".env"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  $file : ${GREEN}✅ Found${NC}"
    else
        echo -e "  $file : ${RED}❌ Missing${NC}"
        ALL_PASSED=false
    fi
done

echo ""
echo -e "${CYAN}======================================${NC}"

if [ "$ALL_PASSED" = true ]; then
    echo -e "${GREEN}✅ All checks passed! Deployment is successful.${NC}"
    echo ""
    echo -e "${CYAN}🌐 Your application is ready:${NC}"
    echo "   Frontend: $FRONTEND_URL"
    echo "   Backend API: $API_URL/api"
    echo ""
    echo -e "${YELLOW}📝 Next steps:${NC}"
    echo "   1. Create an admin user: docker-compose exec backend python create_admin.py"
    echo "   2. Configure SSL/TLS for production"
    echo "   3. Set up monitoring and backups"
    echo "   4. Review SECURITY_CHECKLIST.md"
    exit 0
else
    echo -e "${RED}❌ Some checks failed. Please review the errors above.${NC}"
    echo ""
    echo -e "${YELLOW}📚 Troubleshooting:${NC}"
    echo "   - Check logs: docker-compose logs -f"
    echo "   - Verify .env configuration"
    echo "   - Ensure all services are running"
    echo "   - Review PRODUCTION_DEPLOYMENT.md"
    exit 1
fi
