
import os
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_vertex_connection():
    print("=== DIAGNOSTICO DE ISOLAMENTO VERTEX AI ===")
    
    # 1. Environment Dump (Sanitized)
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    # FORCE us-central1 for diagnostic, ignoring env var if it is 'global'
    env_location = os.getenv("VERTEX_AI_LOCATION")
    location = "us-central1"
    
    print("1. ENV VARS:")
    print(f"   - GOOGLE_CLOUD_PROJECT: {project_id}")
    print(f"   - VERTEX_AI_LOCATION (Raw): {env_location}")
    print(f"   - LOCATION (Forced): {location}")
    print(f"   - GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")

    if not project_id:
        print("❌ ERRO CRÍTICO: GOOGLE_CLOUD_PROJECT não definido.")
        return

    # 2. Import Check
    print("\n2. IMPORTANDO SDK...")
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        print(f"   ✅ Vertex AI SDK importado. Versão: {vertexai.__version__ if hasattr(vertexai, '__version__') else 'unknown'}")
    except ImportError as e:
        print(f"❌ FALHA NO IMPORT: {e}")
        return

    # 3. Initialization
    print(f"\n3. INICIALIZANDO (Project: {project_id}, Location: {location})...")
    try:
        vertexai.init(project=project_id, location=location)
        print("   ✅ vertexai.init() executado sem exceção.")
    except Exception as e:
        print(f"❌ FALHA NA INICIALIZAÇÃO: {e}")
        traceback.print_exc()
        return

    # 4. Model Listing (Discovery)
    print("\n4. TENTATIVA DE LISTAGEM DE MODELOS (via ModelGarden/Service)...")
    try:
        from google.cloud import aiplatform
        aiplatform.init(project=project_id, location=location)
        # List PUBLISHER models (Google's models)
        print("   ℹ️ Consultando Model Garden (Publisher Models)...")
        # Note: listing publisher models via SDK can be verbose, we try to grab one
        try:
            # Try to get a specific model reference to see if it resolves
            from google.cloud.aiplatform import Model
            # This is for custom models. For Generative, we check if we can reach the service.
            pass
        except (ImportError, AttributeError):
            pass
            
    except Exception as e:
        print(f"   ⚠️ Falha ao listar modelos: {e}")

    # 5. Generative Model Probe (Smoke Test)
    # Testing 2026 Model Generation
    models_to_test = [
        "gemini-3.0-pro-001",
        "gemini-3.0-flash-001",
        "gemini-3.0-pro",
        "gemini-3.0-flash"
    ]

    for model_name in models_to_test:
        print(f"\n5. TESTANDO INFERÊNCIA COM: {model_name}")
        try:
            model = GenerativeModel(model_name)
            response = model.generate_content("Say 'Hello Vertex' if you can hear me.")
            print(f"   ✅ SUCESSO! Resposta: {response.text}")
            return # Sair no primeiro sucesso
        except Exception as e:
            print(f"   ❌ FALHA ({model_name}): {str(e)}")
            # Se for 404, imprime detalhes
            if "404" in str(e):
                print("      -> DIAGNÓSTICO: O endpoint retornou 404. O SDK montou a URL errada ou o projeto não tem acesso.")

if __name__ == "__main__":
    debug_vertex_connection()
