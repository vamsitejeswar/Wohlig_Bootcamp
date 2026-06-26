# No-Code Agent Designer vs ADK Code Agents
**Wohlig Internal Comparison | June 2026**

---

## What We Built

| | Gemini Enterprise Agent Designer | ADK Multi-Agent (Day 9) |
|---|---|---|
| Agent | Bootcamp HR Policy Assistant | BI Co-Pilot Orchestrator |
| Knowledge base | Google Drive (HR documents) | Vertex AI Vector Search + BigQuery |
| Built with | Browser UI — no code | Python, Google ADK, Vertex AI |
| Time to build | ~30 minutes | ~2–3 days |
| Code written | 0 lines | ~500 lines across 5 files |

---

## Side-by-Side Comparison

| Dimension | Agent Designer (No-Code) | ADK (Code) |
|---|---|---|
| **Setup time** | 30 minutes | 2–3 days |
| **Who can build it** | Business analyst, HR team, any Google Workspace user | Python developer with Vertex AI knowledge |
| **Data sources** | Google Drive, SharePoint, web (connectors provided) | Any source — BigQuery, GCS, APIs, PDFs, custom |
| **Customisation** | Instructions + examples only | Full control — custom tools, routing logic, retry, validation |
| **Multi-agent support** | No — single agent | Yes — orchestrator routes to multiple sub-agents |
| **SQL / live data** | No | Yes — text-to-SQL, BigQuery execution |
| **Deployment** | Instant — publish to Agent Gallery | Requires `adk web` or Cloud Run deployment |
| **Maintenance** | Update instructions via UI | Update code, redeploy |
| **Cost** | Gemini Enterprise licence (per user) | GCP compute + API costs (pay per use) |
| **Debugging** | Basic — Traces tab in console | Full — ADK Dev UI, event streaming, logs |
| **Version control** | None | Git — full history of every change |

---

## When to Recommend Agent Designer (No-Code)

Use Agent Designer when the client:
- Wants results **in days, not weeks**
- Has **non-technical teams** (HR, Legal, Finance) who will own the agent
- Data is already in **Google Drive or SharePoint**
- Questions are **document lookup only** — policy Q&A, procedure search, FAQ
- Does not need live database queries or real-time data
- Budget is **fixed** (Gemini Enterprise licence covers it)

**Best fit client scenarios:**
- HR policy chatbot for employees
- Legal clause lookup agent
- Onboarding FAQ assistant
- Internal knowledge base Q&A
- Sales playbook assistant

---

## When to Recommend ADK (Code)

Use ADK when the client:
- Needs **live data** from BigQuery, APIs, or databases
- Requires **multi-step reasoning** — e.g., "compare this metric against the policy threshold"
- Needs **custom tools** — sending emails, updating CRM, triggering workflows
- Wants **full audit trail** and version control of agent behaviour
- Has engineering capacity to maintain the system
- Needs **multi-agent orchestration** — one agent routes to multiple specialists

**Best fit client scenarios:**
- BI Co-Pilot (text-to-SQL + document search)
- Customer support agent with CRM integration
- Financial reporting assistant with live BigQuery data
- Document governance with automated approval workflows
- Any agent that needs to DO something, not just answer questions

---

## Wohlig Pitch Summary

> **Agent Designer** = Fast, no-code, for business users who own their data in Drive.
> Pitch it to clients who want a working prototype in a day.

> **ADK** = Powerful, flexible, for engineering-backed products that need live data, tools, and multi-agent logic.
> Pitch it to clients who want a production-grade, maintainable AI system.

Both can co-exist: start with Agent Designer to prove value quickly, then migrate to ADK when complexity grows.
