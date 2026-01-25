import inspect
from google import genai


def dump_docs():
    print("📘 **SDK Documentation Dump**")
    print("-" * 50)

    try:
        client = genai.Client()
        print(f"Client: {client}")

        # Async Models
        print("\n[Async Client]")
        if hasattr(client, "aio"):
            print(f"client.aio: {client.aio}")
            if hasattr(client.aio, "models"):
                print(f"client.aio.models: {client.aio.models}")
                method = getattr(client.aio.models, "generate_content_stream", None)
                if method:
                    print("\n📜 docstring for aio.models.generate_content_stream:")
                    print(method.__doc__)
                    print(f"\nSignature: {inspect.signature(method)}")
                else:
                    print("❌ generate_content_stream NOT FOUND on aio.models")
        else:
            print("❌ client.aio NOT FOUND")

        # Sync Models (Reference)
        print("\n[Sync Client]")
        if hasattr(client, "models"):
            method_sync = getattr(client.models, "generate_content_stream", None)
            if method_sync:
                print("\n📜 docstring for models.generate_content_stream:")
                print(inspect.signature(method_sync))
            else:
                print("❌ generate_content_stream NOT FOUND on models")

    except Exception as e:
        print(f"Dump Failed: {e}")


if __name__ == "__main__":
    dump_docs()
