# AI Model Optimization Configuration
# Model quantization and optimization for <200ms inference

# Vertex AI Endpoint Configuration for Optimized Models
resource "google_vertex_ai_endpoint" "optimized_endpoints" {
  for_each = toset(["us-central1", "europe-west1", "asia-southeast1"])

  name         = "vertice-ai-optimized-${each.key}"
  display_name = "Vertice AI Optimized Endpoint ${each.key}"
  location     = each.key

  # Model deployment with optimization
  deployed_models {
    model = google_vertex_ai_model.optimized_model.id

    # Performance optimization settings
    dedicated_resources {
      machine_spec {
        machine_type = "n1-standard-4"
        accelerator_type  = "NVIDIA_TESLA_T4"
        accelerator_count = 1
      }
      min_replica_count = 1
      max_replica_count = 10

      # Autoscaling based on latency
      autoscaling_metric_specs {
        metric_name = "aiplatform.googleapis.com/prediction/online/serving_infra/latency"
        target      = 200000  # 200ms in microseconds
      }
    }

    # Enable optimization features
    enable_access_logging = true
    enable_container_logging = true
  }

  # Traffic splitting for gradual rollout
  traffic_split {
    "optimized" = 100
  }

  labels = {
    environment = "production"
    optimization = "latency"
  }
}

# Optimized Model Configuration
resource "google_vertex_ai_model" "optimized_model" {
  name        = "vertice-gemini-optimized"
  display_name = "Vertice Gemini Optimized"
  location    = "us-central1"

  # Use optimized container with quantization
  container_spec {
    image_uri = "us-central1-docker.pkg.dev/vertex-ai/llm-containers/stable-diffusion:predictor@sha256:1234567890abcdef"
    args       = ["--model-path", "gs://vertice-models/optimized", "--quantize", "int8", "--cache-size", "4GB"]
    env {
      name  = "MODEL_OPTIMIZATION"
      value = "latency"
    }
    env {
      name  = "MAX_SEQUENCE_LENGTH"
      value = "2048"
    }
    env {
      name  = "BATCH_SIZE"
      value = "4"
    }
  }

  # Model optimization settings
  optimization_config {
    optimization_goal = "LATENCY"
    optimization_level = "AGGRESSIVE"

    # Quantization for faster inference
    quantization_config {
      mode = "DYNAMIC"
      precision = "INT8"
    }

    # Compilation for target hardware
    compilation_config {
      accelerator_type = "NVIDIA_TESLA_T4"
      optimization_level = "MAXIMUM"
    }
  }

  # Version control
  version_aliases = ["optimized", "production"]
  version_description = "Optimized for <200ms global latency"
}
