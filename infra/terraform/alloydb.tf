resource "google_alloydb_cluster" "vertice_memory_cluster" {
  cluster_id = "vertice-memory-cluster"
  location   = var.region

  network_config {
    network = google_compute_network.vertice_vpc.id
  }

  initial_user {
    password = var.alloydb_initial_password
  }

  depends_on = [google_service_networking_connection.private_vpc_connection]
}

resource "google_alloydb_instance" "vertice_memory_primary" {
  cluster       = google_alloydb_cluster.vertice_memory_cluster.name
  instance_id   = "vertice-memory-primary"
  instance_type = "PRIMARY"

  machine_config {
    cpu_count = 4 # Minimum for Vector Search performance
  }

  # Critical: Enable Vertex AI Integration
  database_flags = {
    "google_ml_integration.enable_model_support" = "on"
  }
}
