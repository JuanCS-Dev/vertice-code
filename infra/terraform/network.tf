# VPC Network
resource "google_compute_network" "vertice_vpc" {
  name                    = "vertice-vpc"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.apis]
}

# Subnet for Cloud Run Direct VPC Egress
resource "google_compute_subnetwork" "vertice_subnet" {
  name          = "vertice-subnet"
  ip_cidr_range = "10.0.0.0/24" # Enough for Cloud Run instances
  region        = var.region
  network       = google_compute_network.vertice_vpc.id
}

# Private Service Access (Allocated IP Range for AlloyDB)
resource "google_compute_global_address" "private_ip_alloc" {
  name          = "vertice-psa-range"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vertice_vpc.id
}

# Private Service Access (Connection)
resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vertice_vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]
}
