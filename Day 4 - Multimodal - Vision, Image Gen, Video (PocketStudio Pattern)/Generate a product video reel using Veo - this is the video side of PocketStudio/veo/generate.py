import os
import time
from pathlib import Path
from dotenv import load_dotenv

from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(
    vertexai=True,
    project=os.getenv("PROJECT_ID", ""),
    location=os.getenv("LOCATION", "us-central1")
)

VEO_MODEL = os.getenv("MODEL_NAME", "veo-3.1-generate-001")
BASE_DIR = Path(__file__).parent
ITERATIONS_DIR = BASE_DIR / "iterations"
REFERENCE_IMAGE = BASE_DIR / "reference.png"


def generate_video(prompt: str, output_path: Path):
    with open(REFERENCE_IMAGE, "rb") as img:
        image_bytes = img.read()

    print("Reference image loaded")

    operation = client.models.generate_videos(
        model=VEO_MODEL,
        prompt=prompt,
        image=types.Image(
            image_bytes=image_bytes,
            mime_type="image/png"
        ),
        config=types.GenerateVideosConfig(
            duration_seconds=8
        )
    )

    print("Generating video...")

    while not operation.done:
        time.sleep(10)
        print("Waiting for generation...")
        operation = client.operations.get(operation)

    if operation.error:
        print("Generation failed:")
        print(operation.error)
        return

    video_response = operation.response
    generated_video = video_response.generated_videos[0]
    generated_video.video.save(str(output_path))

    print(f"Video saved at: {output_path}")


def run():
    ITERATIONS_DIR.mkdir(exist_ok=True)

    for version in ["v1", "v2", "v3"]:
        version_dir = ITERATIONS_DIR / version
        version_dir.mkdir(exist_ok=True)

        prompt_file = version_dir / "prompt.txt"
        if not prompt_file.exists():
            print(f"Missing prompt file: {prompt_file}")
            continue

        prompt = prompt_file.read_text().strip()
        print(f"Reading prompt from: {prompt_file}")

        generate_video(prompt, version_dir / "output.mp4")

    print("Done - all iterations generated.")


if __name__ == "__main__":
    run()
