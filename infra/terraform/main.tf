terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  backend "gcs" {
    bucket = "vertice-tf-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Variables (to be defined in terraform.tfvars)
variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "The default GCP region"
  type        = string
  default     = "us-central1"
}

variable "alloydb_initial_password" {
  description = "Initial password for the AlloyDB cluster primary user."
  type        = string
  sensitive   = true
}

# The Foundation: APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "aiplatform.googleapis.com",        # Vertex AI
    "run.googleapis.com",               # Cloud Run
    "alloydb.googleapis.com",           # AlloyDB
    "compute.googleapis.com",           # Networking
    "servicenetworking.googleapis.com", # Private Service Access (PSA)
    "vpcaccess.googleapis.com",         # Serverless VPC Access Connector
    "secretmanager.googleapis.com",     # Secrets
    "cloudbuild.googleapis.com",        # CI/CD
    "artifactregistry.googleapis.com"   # Python Packages
  ])

  service            = each.key
  disable_on_destroy = false
}
