import vertexai
from vertexai.generative_models import GenerativeModel
import os


def list_models():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "vertice-ai")
    location = os.getenv("VERTEX_AI_LOCATION", "us-central1")

    print(f"Listing models for {project_id} @ {location}...")

    vertexai.init(project=project_id, location=location)

    # Unfortunately, the Python SDK doesn't have a simple 'list_models' for GenerativeModel class directly
    # mirroring the Model Garden list. We often have to try common names or use the Model Registry API.
    # However, we can use the lower-level API.

    from google.cloud import aiplatform

    aiplatform.init(project=project_id, location=location)

    try:
        models = aiplatform.Model.list()
        print("\nDeployed Models (Custom):")
        for m in models:
            print(f"- {m.display_name} ({m.resource_name})")
    except Exception as e:
        print(f"Failed to list custom models: {e}")

    # For Foundation Models, we verify specific IDs manually since there isn't a clean "List All Foundation Models"
    # in the high-level SDK without iterating PublisherModel.

    candidates = [
        "gemini-3-flash",
        "gemini-3-pro",
        "gemini-3-flash-preview",
        "gemini-3-pro-preview",
    ]

    print("\nVerifying Foundation Model Availability:")
    for model_id in candidates:
        try:
            model = GenerativeModel(model_id)
            # Try a dry run (count tokens is cheap/fast)
            res = model.count_tokens("Test")
            print(f"✅ {model_id} IS AVAILABLE (Tokens: {res.total_tokens})")
        except Exception as e:
            print(f"❌ {model_id} NOT AVAILABLE: {e}")


if __name__ == "__main__":
    list_models()
