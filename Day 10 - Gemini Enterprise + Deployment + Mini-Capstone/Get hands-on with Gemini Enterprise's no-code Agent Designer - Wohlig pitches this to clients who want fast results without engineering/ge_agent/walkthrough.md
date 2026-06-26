# Gemini Enterprise — HR Policy Agent Walkthrough
**Built by:** Vamsi Padmaraju | **Date:** June 26, 2026
**Platform:** Gemini Enterprise (Google Cloud — Wohlig project)

---

## Overview

This document walks through the complete process of building a no-code HR Policy AI Agent using Gemini Enterprise. The agent answers employee HR questions by reading documents from Google Drive — no Python, no ADK, no deployment code required.

---

## Step 1 — Access Gemini Enterprise

**Where:** Google Cloud Console → Gemini Enterprise
**URL:** `console.cloud.google.com/gemini-enterprise`
**Project:** Wohlig

Gemini Enterprise is Google's no-code enterprise AI platform. It has three core sections:
- **Apps** — the Gemini Enterprise assistant instances
- **Data stores** — the knowledge bases (Google Drive, SharePoint, web, etc.)
- **Agents** — AI agents added to the assistant

> Screenshot 1: Gemini Enterprise Data stores page showing "+ Create data store" button

---

## Step 2 — Create OAuth Credentials for Google Drive

Before connecting Google Drive as a data source, you need OAuth 2.0 credentials from Google Cloud.

**Where:** Google Cloud Console → APIs & Services → Credentials

**Steps:**
1. Go to **APIs & Services → Credentials**
2. Click **"+ Create Credentials" → "OAuth 2.0 Client ID"**
3. Application type: **Web application**
4. Name: `Vamsi Drive`
5. Under **Authorized redirect URIs**, add the redirect URI shown in Gemini Enterprise's data store creation screen:
   `https://vertexaisearch.cloud.google.com/oauth-redirect`
6. Click **Save**
7. Copy the **Client ID** and **Client Secret** shown on the right panel

> Screenshot 2: Google Cloud Console — APIs & Services → Credentials page with "+ Create credentials" button

> Screenshot 3: OAuth 2.0 Client ID details page showing Client ID, Client Secret, and Authorized redirect URIs (vertexaisearch.cloud.google.com/oauth-redirect)

---

## Step 3 — Create a Google Drive Data Store

**Where:** Gemini Enterprise → Data stores → Create data store

**Steps:**
1. In Gemini Enterprise left sidebar, click **"Data stores"**
2. Click **"+ Create data store"**
3. In the Source search box, type `drive`
4. Select **"Google Drive"** from First-party data sources
5. Click **"Add data source"**
6. On the next screen (Authentication settings):
   - Paste your **Client ID**
   - Paste your **Client Secret**
   - Click **"Verify Auth"** → it opens a Google login popup
   - Approve access to your Drive
7. Click **Continue**
8. Select the HR documents folder from your Google Drive
9. Name the data store: `Vamsi Drive`
10. Click **Create**

The data store ID generated: `vamsi-drive_1782467704341`

> Screenshot 4: Create data store → Source step, searching "drive", showing Google Drive as first-party data source

> Screenshot 5: Create data store → Data step, showing Client ID and Client Secret fields with the tutorial panel explaining the Google Drive connection

---

## Step 4 — Verify Data Store Created

After creation, the data store appears in the Connected data stores list:

| Name | Type | Connected apps | Created | ID | Location |
|---|---|---|---|---|---|
| Vamsi Drive | Google Drive | N/A | Jun 26, 2026 | vamsi-drive_1782467704341 | global |

> Screenshot 6: Connected data stores list showing "Vamsi Drive" successfully created

---

## Step 5 — Open Agent Designer

**Where:** Gemini Enterprise App → Agents → Agent Designer

**Steps:**
1. Click **"Apps"** in the left sidebar
2. Open the **"Wohlig GE"** app
3. Click **"Agents"** in the app sidebar
4. Click **"+ Add agent"** → you see agent type options
5. For no-code: skip the "Add agent" modal and instead open the **Agent Designer** directly from the Gemini Enterprise user interface (vertexaisearch.cloud.google.com)

> Screenshot 7: Agent Designer interface showing "My Agent" node on canvas with Details panel open on the right (Name, Description, Instructions fields)

---

## Step 6 — Configure the Agent

In the Agent Designer Details panel, fill in:

**Name:**
```
Bootcamp HR Policy Assistant
```

**Description:**
```
An AI assistant that answers employee questions about Wohlig HR policies including leave, expenses, onboarding, travel, benefits, and workplace guidelines using official company documents.
```

**Instructions:**
```
You are an HR Policy Assistant for Wohlig employees.

Answer questions only from the connected HR documents. Never use outside knowledge.
Always mention which document your answer is from.
If the answer is not in the documents, say: "This is not covered in the current HR policy documents. Please contact HR directly."
Keep answers short and use bullet points for multi-step answers.
Do not approve or reject any employee requests — only explain the policy.
```

After filling in instructions:
1. Click the **data store icon** or **"+" tool** to attach a data source
2. Select the Google Drive data store
3. Click **"Create"** (top right)

---

## Step 7 — Test the Agent

**Where:** vertexaisearch.cloud.google.com — Bootcamp HR Policy Assistant chat

Open the agent chat and run test queries. The agent searches the connected Google Drive documents and responds with cited answers.

**Test query:** `get the leave policy`

**Agent response:**
> According to the Leave Policy, you are entitled to the following:
> - 12 days of casual leave
> - 12 days of sick leave
> - 15 days of earned leave
>
> Unused casual and sick leave will lapse at the end of the year, while earned leave can be carried forward, up to a maximum of 45 days.

> Screenshot 8: Bootcamp HR Policy Assistant chat — agent responding to "get the leave policy" with correct leave entitlements from the HR documents

---

## Step 8 — Publish to Agent Gallery

**Steps:**
1. In the admin console → Agents → find your agent
2. Click the **three-dot menu (⋮)** → **"Publish"**
3. Set visibility: **Organisation** (so all Wohlig employees can use it)
4. Click **Publish**
5. Copy the agent URL from the browser address bar

The agent is now available to all users in the Wohlig GE instance under **Agents → Our agents**.

---

## Summary of What Was Built

| Component | Details |
|---|---|
| Platform | Gemini Enterprise (Google Cloud — Wohlig) |
| Data source | Google Drive (Vamsi Drive data store) |
| Agent type | No-code (Agent Designer) |
| Agent name | Bootcamp HR Policy Assistant |
| Knowledge base | HR policy documents in Google Drive |
| Time to build | ~30 minutes (no code written) |

---

## Key Observations

- **No code required** — the entire agent was built through browser UIs
- **OAuth setup is the hardest step** — getting Client ID + Secret from Google Cloud takes ~5 minutes
- **Data store conflict** — you cannot mix unscoped (default ge-gdrive) and admin-scoped Drive connectors in the same engine; use one type only
- **Agent Designer** is separate from the admin console — it is accessed from the user-facing Gemini Enterprise app
- **Response quality** is good for factual policy questions; the agent correctly cited leave entitlements from the HR documents
