output "cluster_private_ip" {
  description = "Primary AlloyDB instance private IP address."
  value       = google_alloydb_instance.vertice_memory_primary.ip_address
}

output "network_name" {
  description = "VPC Network Name"
  value       = google_compute_network.vertice_vpc.name
}

output "subnet_name" {
  description = "Subnet Name for Direct VPC Egress"
  value       = google_compute_subnetwork.vertice_subnet.name
}
