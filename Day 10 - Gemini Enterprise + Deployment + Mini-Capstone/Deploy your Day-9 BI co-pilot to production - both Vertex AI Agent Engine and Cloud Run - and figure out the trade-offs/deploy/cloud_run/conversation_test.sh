#!/bin/bash
# deploy/cloud_run/conversation_test.sh
# ---------------------------------------
# Runs the same 5-turn conversation against the Cloud Run endpoint.
# Set CLOUD_RUN_URL before running.
#
# Usage:
#   export CLOUD_RUN_URL=https://bi-copilot-xxx-uc.a.run.app
#   ./conversation_test.sh

set -e

URL="${CLOUD_RUN_URL:-http://localhost:8080}"

echo "=== BI Co-Pilot — 5-Turn Conversation Test ==="
echo "Endpoint: $URL"
echo ""

# Create a session for multi-turn
SESSION_ID=$(curl -s -X POST "${URL}/session/create" \
    -H "Content-Type: application/json" | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")
echo "Session ID: $SESSION_ID"
echo ""

ask() {
    local label="$1"
    local question="$2"
    echo "--- ${label} ---"
    echo "Q: ${question}"
    RESPONSE=$(curl -s -X POST "${URL}/query" \
        -H "Content-Type: application/json" \
        -d "{\"question\": \"${question}\", \"session_id\": \"${SESSION_ID}\"}")
    echo "A: $(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['answer'][:300])")"
    echo ""
}

ask "Q1 — BQ only"  "How many trips happened last month?"
ask "Q2 — RAG only" "What is the data retention policy for trip records?"
ask "Q3 — Both"     "Did last month average trip duration exceed the service standard?"
ask "Q4 — BQ only"  "Which vendor had the highest average fare in Q3?"
ask "Q5 — Both"     "What are the SLA targets for data pipeline uptime and did we meet them last month?"

echo "=== Done ==="
echo "View traces: https://console.cloud.google.com/traces/list?project=wohlig"
