import os
from dotenv import load_dotenv

# Set Vertex AI flag directly in os.environ before ADK creates any LLM client.
# load_dotenv alone is not reliable enough — ADK may read env vars earlier.
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "wohlig")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")

# Load the rest of the env vars from the project .env
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from .orchestrator import root_agent  # noqa: F401
