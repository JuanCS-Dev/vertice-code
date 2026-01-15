# Cloud CDN Configuration for AI Inference Latency Optimization
# Global edge caching to achieve <200ms latency worldwide

resource "google_compute_backend_bucket" "ai_cache" {
  name        = "vertice-ai-cache"
  bucket_name = "vertice-ai-cache-bucket"
  enable_cdn  = true

  cdn_policy {
    cache_mode = "CACHE_ALL_STATIC"
    default_ttl = 3600  # 1 hour
    max_ttl     = 86400 # 24 hours
    client_ttl  = 3600

    # AI-specific optimizations
    cache_key_policy {
      include_host         = true
      include_protocol     = true
      include_query_string = false
      include_http_headers = ["x-region", "x-user-id"]
    }

    # Negative caching for errors
    negative_caching = true
    negative_caching_policy {
      code = 404
      ttl  = 300
    }
  }
}

resource "google_compute_url_map" "ai_routing" {
  name = "vertice-ai-url-map"

  default_service = google_compute_backend_service.vertex_ai_global.id

  host_rule {
    hosts        = ["ai-api.vertice-maximus.com"]
    path_matcher = "ai-paths"
  }

  path_matcher {
    name = "ai-paths"

    # Cache AI responses at edge
    path_rule {
      paths   = ["/api/v1/ai/*"]
      service = google_compute_backend_bucket.ai_cache.id
    }

    # Direct to AI service for dynamic requests
    path_rule {
      paths   = ["/api/v1/ai/stream", "/api/v1/ai/chat"]
      service = google_compute_backend_service.vertex_ai_global.id
    }
  }
}

resource "google_compute_target_https_proxy" "ai_proxy" {
  name             = "vertice-ai-https-proxy"
  url_map          = google_compute_url_map.ai_routing.id
  ssl_certificates = [google_compute_ssl_certificate.ai_cert.id]
}

resource "google_compute_global_address" "ai_ip" {
  name = "vertice-ai-global-ip"
}

resource "google_compute_global_forwarding_rule" "ai_forwarding" {
  name       = "vertice-ai-forwarding-rule"
  target     = google_compute_target_https_proxy.ai_proxy.id
  port_range = "443"
  ip_address = google_compute_global_address.ai_ip.address
}