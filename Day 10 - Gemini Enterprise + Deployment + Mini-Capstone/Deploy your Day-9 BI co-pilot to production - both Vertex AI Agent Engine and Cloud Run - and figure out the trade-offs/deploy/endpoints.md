# Live Endpoints

## Vertex AI Agent Engine

**Resource name:**
```
projects/wohlig/locations/us-central1/reasoningEngines/<YOUR_ID>
```
*(Fill in after running `deploy/agent_engine/deploy.py`)*

**Query via Python:**
```python
import vertexai
from vertexai.preview import reasoning_engines

vertexai.init(project="wohlig", location="us-central1")
engine = reasoning_engines.ReasoningEngine("projects/wohlig/locations/us-central1/reasoningEngines/<ID>")
session = engine.create_session(user_id="test")

for event in engine.stream_query(
    user_id="test",
    session_id=session["id"],
    message="How many trips happened last month?",
):
    print(event)
```

---

## Cloud Run

**Live URL:**
```
https://bi-copilot-<hash>-uc.a.run.app
```
*(Fill in after running `deploy/cloud_run/deploy.sh`)*

**Health check:**
```bash
curl https://bi-copilot-<hash>-uc.a.run.app/health
# {"status": "ok", "agent": "bi_copilot_orchestrator"}
```

**Single query:**
```bash
curl -X POST https://bi-copilot-<hash>-uc.a.run.app/query \
  -H "Content-Type: application/json" \
  -d '{"question": "How many trips happened last month?"}'
```

**Multi-turn conversation:**
```bash
# Step 1 — create session
SESSION=$(curl -s -X POST https://bi-copilot-<hash>-uc.a.run.app/session/create \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])")

# Step 2 — ask questions in the same session
curl -X POST https://bi-copilot-<hash>-uc.a.run.app/query \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"Which vendor had the highest fare in Q3?\", \"session_id\": \"$SESSION\"}"

curl -X POST https://bi-copilot-<hash>-uc.a.run.app/query \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"What is the data retention policy?\", \"session_id\": \"$SESSION\"}"
```

---

## Cloud Trace Dashboard
```
https://console.cloud.google.com/traces/list?project=wohlig
```
Filter by service name: `bi-copilot` or `bi_copilot_orchestrator`
