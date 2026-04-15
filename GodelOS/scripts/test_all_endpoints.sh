#!/bin/bash
# GödelOS API Endpoint Test Script
# Tests all available endpoints to ensure they're working correctly

BASE_URL="http://localhost:8000"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🧪 GödelOS API Endpoint Test Suite${NC}"
echo "======================================="
echo "Testing server at: $BASE_URL"
echo ""

# Function to test an endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    
    echo -e "Testing: ${YELLOW}$description${NC}"
    echo "Endpoint: $method $endpoint"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "%{http_code}" -o /tmp/response.json "$BASE_URL$endpoint")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" -o /tmp/response.json "$BASE_URL$endpoint")
    fi
    
    http_code="${response: -3}"
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "201" ]; then
        echo -e "${GREEN}✅ SUCCESS (HTTP $http_code)${NC}"
        echo "Response:"
        cat /tmp/response.json | jq '.' 2>/dev/null || cat /tmp/response.json
    else
        echo -e "${RED}❌ FAILED (HTTP $http_code)${NC}"
        echo "Error Response:"
        cat /tmp/response.json
    fi
    echo ""
    echo "---"
    echo ""
}

# Health and Status Endpoints
echo -e "${YELLOW}🏥 Health & Status Endpoints${NC}"
test_endpoint "GET" "/api/health" "" "Basic Health Check"
test_endpoint "GET" "/api/status" "" "System Status"
test_endpoint "GET" "/api/enhanced-cognitive/health" "" "Enhanced Cognitive Health"
test_endpoint "GET" "/api/enhanced-cognitive/status" "" "Enhanced Cognitive Status"
test_endpoint "GET" "/api/enhanced-cognitive/stream/status" "" "Enhanced Cognitive Stream Status"

# Cognitive State Endpoints
echo -e "${YELLOW}🧠 Cognitive State Endpoints${NC}"
test_endpoint "GET" "/api/cognitive-state" "" "Get Cognitive State"

# Knowledge Management Endpoints
echo -e "${YELLOW}📚 Knowledge Management Endpoints${NC}"
test_endpoint "GET" "/api/knowledge/concepts" "" "Get Knowledge Concepts"
test_endpoint "GET" "/api/knowledge/graph" "" "Get Knowledge Graph"
test_endpoint "GET" "/api/transparency/knowledge-graph/export" "" "Export Knowledge Graph"

# Query Processing Endpoints
echo -e "${YELLOW}🔍 Query Processing Endpoints${NC}"
test_endpoint "POST" "/api/query" '{"query": "What is the meaning of life?", "context": {"user": "test"}}' "Process Query"
test_endpoint "POST" "/api/enhanced-cognitive/query" '{"query": "Test enhanced query", "reasoning_trace": true}' "Enhanced Cognitive Query"

# LLM Integration Endpoints
echo -e "${YELLOW}🤖 LLM Integration Endpoints${NC}"
test_endpoint "POST" "/api/llm-chat/message" '{"message": "Hello, how are you?"}' "LLM Chat Message"
test_endpoint "GET" "/api/llm-chat/capabilities" "" "LLM Chat Capabilities"

# Metacognition Endpoints
echo -e "${YELLOW}🤔 Metacognition Endpoints${NC}"
test_endpoint "GET" "/api/metacognition/status" "" "Metacognition Status"
test_endpoint "POST" "/api/metacognition/reflect" '{"trigger": "test_reflection", "context": {"test": true}}' "Trigger Reflection"

# Tool Integration Endpoints
echo -e "${YELLOW}🛠️ Tool Integration Endpoints${NC}"
test_endpoint "GET" "/api/tools/available" "" "Available Tools"

# Transparency Endpoints
echo -e "${YELLOW}🔍 Transparency Endpoints${NC}"
test_endpoint "GET" "/api/transparency/reasoning-trace" "" "Reasoning Trace"
test_endpoint "GET" "/api/transparency/decision-history" "" "Decision History"

# File Processing Endpoints
echo -e "${YELLOW}📁 File Processing Endpoints${NC}"
# Note: File upload endpoints require multipart/form-data, testing with a simple text file
echo "Creating test file..."
echo "This is a test file for GödelOS" > /tmp/test_file.txt

echo -e "Testing: ${YELLOW}File Upload${NC}"
echo "Endpoint: POST /api/files/upload"
upload_response=$(curl -s -w "%{http_code}" -X POST -F "file=@/tmp/test_file.txt" -o /tmp/upload_response.json "$BASE_URL/api/files/upload")
upload_code="${upload_response: -3}"

if [ "$upload_code" = "200" ] || [ "$upload_code" = "201" ]; then
    echo -e "${GREEN}✅ SUCCESS (HTTP $upload_code)${NC}"
    cat /tmp/upload_response.json | jq '.' 2>/dev/null || cat /tmp/upload_response.json
else
    echo -e "${RED}❌ FAILED (HTTP $upload_code)${NC}"
    cat /tmp/upload_response.json
fi
echo ""
echo "---"
echo ""

echo -e "Testing: ${YELLOW}Knowledge Import from File${NC}"
echo "Endpoint: POST /api/knowledge/import/file"
import_response=$(curl -s -w "%{http_code}" -X POST -F "file=@/tmp/test_file.txt" -o /tmp/import_response.json "$BASE_URL/api/knowledge/import/file")
import_code="${import_response: -3}"

if [ "$import_code" = "200" ] || [ "$import_code" = "201" ]; then
    echo -e "${GREEN}✅ SUCCESS (HTTP $import_code)${NC}"
    cat /tmp/import_response.json | jq '.' 2>/dev/null || cat /tmp/import_response.json
else
    echo -e "${RED}❌ FAILED (HTTP $import_code)${NC}"
    cat /tmp/import_response.json
fi
echo ""
echo "---"
echo ""

# Enhanced Cognitive Configuration
echo -e "${YELLOW}⚙️ Configuration Endpoints${NC}"
test_endpoint "POST" "/api/enhanced-cognitive/configure" '{"transparency_level": "high", "reasoning_depth": "detailed", "streaming": true}' "Configure Enhanced Cognitive"

# API Documentation
echo -e "${YELLOW}📖 Documentation Endpoints${NC}"
echo -e "Testing: ${YELLOW}API Documentation${NC}"
echo "Endpoint: GET /docs"
docs_response=$(curl -s -w "%{http_code}" -o /tmp/docs.html "$BASE_URL/docs")
docs_code="${docs_response: -3}"

if [ "$docs_code" = "200" ]; then
    echo -e "${GREEN}✅ SUCCESS (HTTP $docs_code) - Swagger UI Available${NC}"
    echo "Documentation size: $(wc -c < /tmp/docs.html) bytes"
else
    echo -e "${RED}❌ FAILED (HTTP $docs_code)${NC}"
fi
echo ""

# OpenAPI Schema
test_endpoint "GET" "/openapi.json" "" "OpenAPI Schema"

# Cleanup
rm -f /tmp/response.json /tmp/upload_response.json /tmp/docs.html /tmp/test_file.txt

echo -e "${YELLOW}🏁 Test Suite Complete${NC}"
echo "======================================="
echo "Check the results above to see which endpoints are working correctly."
echo ""
echo "To run individual tests, use commands like:"
echo "curl $BASE_URL/api/health"
echo "curl -X POST $BASE_URL/api/query -H 'Content-Type: application/json' -d '{\"query\": \"test\"}'"
echo ""
echo -e "${GREEN}Server is running at: $BASE_URL${NC}"
echo -e "${GREEN}API Documentation: $BASE_URL/docs${NC}"
