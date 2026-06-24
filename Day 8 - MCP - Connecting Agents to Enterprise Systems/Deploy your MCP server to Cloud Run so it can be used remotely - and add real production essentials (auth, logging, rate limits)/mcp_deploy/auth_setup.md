# Auth Setup — How a Client Gets and Rotates an API Key

## How it works
Every request must include the header:
```
x-api-key: <your-key>
```
The server checks it against the `API_KEY` environment variable set in Cloud Run.

---

## Giving a new client an API key

1. Generate a key:
```bash
openssl rand -hex 20
# e.g. → a3f9c2d1e4b5a6f7g8h9i0j1k2l3m4n5o6p7
```

2. Add it to Cloud Run:
```bash
gcloud run services update wohlig-mcp-server \
  --region us-central1 \
  --set-env-vars "API_KEY=<new-key>"
```

3. Share the key with the client securely (never in email — use a secrets manager or 1Password).

---

## Rotating a key (client compromised)

1. Generate a new key (step above)
2. Update Cloud Run env var with the new key
3. Old key stops working immediately — no restart needed
4. Notify the client of their new key

---

## For multiple clients (production upgrade)
Store keys in **Google Secret Manager** and validate against a list instead of a single env var. This allows per-client keys, revocation, and audit logging per key.
