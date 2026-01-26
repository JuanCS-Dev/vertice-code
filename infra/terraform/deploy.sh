#!/bin/bash
set -e

# Initialize Terraform (now with GCS backend)
terraform init

# Try to import the VPC network if it's not in state
if ! terraform state list | grep -q "google_compute_network.vertice_vpc"; then
  echo "Importing existing VPC network..."
  terraform import -var="project_id=$PROJECT_ID" -var="region=us-central1" \
    google_compute_network.vertice_vpc projects/$PROJECT_ID/global/networks/vertice-vpc || echo "Import failed or already managed"
fi

# Try to import the Subnet if it's not in state
if ! terraform state list | grep -q "google_compute_subnetwork.vertice_subnet"; then
  echo "Importing existing Subnet..."
  terraform import -var="project_id=$PROJECT_ID" -var="region=us-central1" \
    google_compute_subnetwork.vertice_subnet projects/$PROJECT_ID/regions/us-central1/subnetworks/vertice-subnet || echo "Import failed or already managed"
fi

# Try to import the Global Address (PSA) if it's not in state
if ! terraform state list | grep -q "google_compute_global_address.private_ip_alloc"; then
  echo "Importing existing PSA Range..."
  terraform import -var="project_id=$PROJECT_ID" -var="region=us-central1" \
    google_compute_global_address.private_ip_alloc projects/$PROJECT_ID/global/addresses/vertice-psa-range || echo "Import failed or already managed"
fi

# Apply the rest (AlloyDB, etc)
echo "Applying Terraform configuration..."
terraform apply -var="project_id=$PROJECT_ID" -var="region=us-central1" -auto-approve
