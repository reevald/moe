#!/bin/bash

# Test script for MOE API endpoints
# Usage: ./test_moe_api.sh

set -e

API_URL="http://localhost:8001/api/v1"

# Get token from container environment
TOKEN=$(docker exec moe-api sh -c 'echo $STATIC_TOKEN')

echo "============================================"
echo "MOE API Test Suite"
echo "============================================"
echo "API URL: $API_URL"
echo "Token: ${TOKEN:0:20}..."
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
echo "GET /health"
curl -s "$API_URL/health" | python3 -m json.tool
echo ""

# Test 2: Get Random Problem
echo "Test 2: Get Random Problem"
echo "GET /moe/problems/random"
RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_URL/moe/problems/random")
echo "$RESPONSE" | python3 -m json.tool
echo ""

# Check if we got a problem
if echo "$RESPONSE" | grep -q '"success":true'; then
    PROBLEM_ID=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['data']['problem_id'])")
    echo "Got problem ID: $PROBLEM_ID"
    echo ""
    
    # Test 3: Get Problem by ID
    echo "Test 3: Get Problem by ID"
    echo "GET /moe/problems/$PROBLEM_ID"
    curl -s -H "Authorization: Bearer $TOKEN" "$API_URL/moe/problems/$PROBLEM_ID" | python3 -m json.tool
    echo ""
    
    # Test 4: Submit Solution
    echo "Test 4: Submit Solution"
    echo "POST /moe/submissions"
    SUBMIT_RESPONSE=$(curl -s -X POST \
        -H "Authorization: Bearer $TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"problem_id\": \"$PROBLEM_ID\", \"solution_latex\": \"\\\\text{This is a test solution}\"}" \
        "$API_URL/moe/submissions")
    echo "$SUBMIT_RESPONSE" | python3 -m json.tool
    echo ""
    
    # Check if submission was created
    if echo "$SUBMIT_RESPONSE" | grep -q '"success":true'; then
        SUBMISSION_ID=$(echo "$SUBMIT_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['data']['submission_id'])")
        echo "Got submission ID: $SUBMISSION_ID"
        echo ""
        
        # Test 5: Get Submission Status
        echo "Test 5: Get Submission Status"
        echo "GET /moe/submissions/$SUBMISSION_ID/status"
        curl -s -H "Authorization: Bearer $TOKEN" "$API_URL/moe/submissions/$SUBMISSION_ID/status" | python3 -m json.tool
        echo ""
        
        # Test 6: Get Submission Result
        echo "Test 6: Get Submission Result"
        echo "GET /moe/submissions/$SUBMISSION_ID/result"
        curl -s -H "Authorization: Bearer $TOKEN" "$API_URL/moe/submissions/$SUBMISSION_ID/result" | python3 -m json.tool
        echo ""
    fi
else
    echo "Failed to get problem, skipping submission tests"
fi

echo "============================================"
echo "Test Suite Complete"
echo "============================================"
