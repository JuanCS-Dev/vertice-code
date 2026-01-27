# =============================================================================
# DIGITAL NERVOUS SYSTEM - EVENTARC INFRASTRUCTURE
# =============================================================================
#
# Terraform configuration for deploying the Nervous System with Eventarc triggers
#
# Components:
# - Service Account with required permissions
# - Eventarc triggers for Cloud Logging, Monitoring, Pub/Sub
# - Pub/Sub topics for nervous system events
# - Cloud Monitoring custom metrics
#
# Deploy: terraform apply -var="project_id=vertice-ai"
# =============================================================================

variable "nervous_system_enabled" {
  description = "Enable Nervous System Eventarc triggers"
  type        = bool
  default     = true
}

# =============================================================================
# SERVICE ACCOUNT
# =============================================================================

resource "google_service_account" "nervous_system" {
  count = var.nervous_system_enabled ? 1 : 0

  account_id   = "nervous-system-sa"
  display_name = "Digital Nervous System Service Account"
  description  = "Service account for NEXUS Digital Nervous System Eventarc triggers"
  project      = var.project_id
}

# Grant Cloud Run invoker role to the service account
resource "google_cloud_run_service_iam_member" "nervous_system_invoker" {
  count = var.nervous_system_enabled ? 1 : 0

  location = var.region
  service  = "vertice-agent-gateway"
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.nervous_system[0].email}"
  project  = var.project_id
}

# Grant required permissions to the service account
resource "google_project_iam_member" "nervous_system_permissions" {
  for_each = var.nervous_system_enabled ? toset([
    "roles/logging.logWriter",
    "roles/logging.viewer",
    "roles/monitoring.metricWriter",
    "roles/monitoring.viewer",
    "roles/cloudtrace.agent",
    "roles/pubsub.subscriber",
    "roles/pubsub.publisher",
    "roles/eventarc.eventReceiver",
  ]) : toset([])

  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.nervous_system[0].email}"
}

# =============================================================================
# PUB/SUB TOPICS FOR NERVOUS SYSTEM
# =============================================================================

resource "google_pubsub_topic" "nervous_system_events" {
  count = var.nervous_system_enabled ? 1 : 0

  name    = "nervous-system-events"
  project = var.project_id

  labels = {
    component = "nervous-system"
    layer     = "eventarc"
  }

  message_retention_duration = "604800s" # 7 days
}

resource "google_pubsub_topic" "nervous_system_alerts" {
  count = var.nervous_system_enabled ? 1 : 0

  name    = "nervous-system-alerts"
  project = var.project_id

  labels = {
    component = "nervous-system"
    layer     = "monitoring"
  }

  message_retention_duration = "604800s"
}

resource "google_pubsub_topic" "nervous_system_escalations" {
  count = var.nervous_system_enabled ? 1 : 0

  name    = "nervous-system-escalations"
  project = var.project_id

  labels = {
    component = "nervous-system"
    layer     = "human-escalation"
  }

  message_retention_duration = "604800s"
}

# Dead letter topic for failed processing
resource "google_pubsub_topic" "nervous_system_dlq" {
  count = var.nervous_system_enabled ? 1 : 0

  name    = "nervous-system-dlq"
  project = var.project_id

  labels = {
    component = "nervous-system"
    layer     = "dead-letter"
  }
}

# =============================================================================
# EVENTARC TRIGGERS
# =============================================================================

# Trigger for Cloud Logging - WARNING and above
resource "google_eventarc_trigger" "logging_warning" {
  count = var.nervous_system_enabled ? 1 : 0

  name     = "nervous-system-logging-warning"
  location = var.region
  project  = var.project_id

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.audit.log.v1.written"
  }

  destination {
    cloud_run_service {
      service = "vertice-agent-gateway"
      region  = var.region
      path    = "/v1/nexus/v1/eventarc/logging"
    }
  }

  service_account = google_service_account.nervous_system[0].email

  labels = {
    component = "nervous-system"
    layer     = "reflex-arc"
  }
}

# Trigger for Cloud Monitoring alerts
resource "google_eventarc_trigger" "monitoring_alerts" {
  count = var.nervous_system_enabled ? 1 : 0

  name     = "nervous-system-monitoring-alerts"
  location = var.region
  project  = var.project_id

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.pubsub.topic.v1.messagePublished"
  }

  transport {
    pubsub {
      topic = google_pubsub_topic.nervous_system_alerts[0].id
    }
  }

  destination {
    cloud_run_service {
      service = "vertice-agent-gateway"
      region  = var.region
      path    = "/v1/nexus/v1/eventarc/monitoring"
    }
  }

  service_account = google_service_account.nervous_system[0].email

  labels = {
    component = "nervous-system"
    layer     = "innate-immunity"
  }
}

# Trigger for Pub/Sub events (nervous system internal)
resource "google_eventarc_trigger" "pubsub_events" {
  count = var.nervous_system_enabled ? 1 : 0

  name     = "nervous-system-pubsub"
  location = var.region
  project  = var.project_id

  matching_criteria {
    attribute = "type"
    value     = "google.cloud.pubsub.topic.v1.messagePublished"
  }

  transport {
    pubsub {
      topic = google_pubsub_topic.nervous_system_events[0].id
    }
  }

  destination {
    cloud_run_service {
      service = "vertice-agent-gateway"
      region  = var.region
      path    = "/v1/nexus/v1/eventarc/pubsub"
    }
  }

  service_account = google_service_account.nervous_system[0].email

  labels = {
    component = "nervous-system"
    layer     = "event-bus"
  }
}

# =============================================================================
# CLOUD MONITORING ALERT POLICIES
# =============================================================================

# Alert for high error rate - triggers nervous system
resource "google_monitoring_alert_policy" "high_error_rate" {
  count = var.nervous_system_enabled ? 1 : 0

  display_name = "Nervous System - High Error Rate"
  project      = var.project_id
  combiner     = "OR"

  conditions {
    display_name = "Error rate > 5%"

    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class=\"5xx\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.05
      duration        = "60s"

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }

  notification_channels = []

  alert_strategy {
    auto_close = "604800s"
  }

  documentation {
    content   = "High error rate detected. Nervous System will attempt autonomous healing."
    mime_type = "text/markdown"
  }

  user_labels = {
    component = "nervous-system"
    severity  = "warning"
  }
}

# Alert for high latency
resource "google_monitoring_alert_policy" "high_latency" {
  count = var.nervous_system_enabled ? 1 : 0

  display_name = "Nervous System - High Latency"
  project      = var.project_id
  combiner     = "OR"

  conditions {
    display_name = "P99 latency > 5s"

    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/request_latencies\""
      comparison      = "COMPARISON_GT"
      threshold_value = 5000
      duration        = "120s"

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_PERCENTILE_99"
        cross_series_reducer = "REDUCE_MEAN"
      }
    }
  }

  notification_channels = []

  user_labels = {
    component = "nervous-system"
    severity  = "warning"
  }
}

# Alert for high memory usage
resource "google_monitoring_alert_policy" "high_memory" {
  count = var.nervous_system_enabled ? 1 : 0

  display_name = "Nervous System - High Memory Usage"
  project      = var.project_id
  combiner     = "OR"

  conditions {
    display_name = "Memory > 90%"

    condition_threshold {
      filter          = "resource.type=\"cloud_run_revision\" AND metric.type=\"run.googleapis.com/container/memory/utilizations\""
      comparison      = "COMPARISON_GT"
      threshold_value = 0.9
      duration        = "60s"

      aggregations {
        alignment_period     = "60s"
        per_series_aligner   = "ALIGN_MEAN"
        cross_series_reducer = "REDUCE_MEAN"
      }
    }
  }

  notification_channels = []

  user_labels = {
    component = "nervous-system"
    severity  = "critical"
  }
}

# =============================================================================
# CUSTOM METRICS FOR NERVOUS SYSTEM
# =============================================================================

resource "google_monitoring_metric_descriptor" "autonomous_resolution_rate" {
  count = var.nervous_system_enabled ? 1 : 0

  description  = "Rate of events resolved autonomously by the Nervous System"
  display_name = "Autonomous Resolution Rate"
  type         = "custom.googleapis.com/nervous_system/autonomous_resolution_rate"
  metric_kind  = "GAUGE"
  value_type   = "DOUBLE"
  project      = var.project_id

  labels {
    key         = "layer"
    value_type  = "STRING"
    description = "Resolution layer (reflex, innate, adaptive, human)"
  }

  labels {
    key         = "service"
    value_type  = "STRING"
    description = "Service name"
  }
}

resource "google_monitoring_metric_descriptor" "nervous_system_latency" {
  count = var.nervous_system_enabled ? 1 : 0

  description  = "Latency of Nervous System event processing by layer"
  display_name = "Nervous System Latency"
  type         = "custom.googleapis.com/nervous_system/latency"
  metric_kind  = "GAUGE"
  value_type   = "DOUBLE"
  unit         = "ms"
  project      = var.project_id

  labels {
    key         = "layer"
    value_type  = "STRING"
    description = "Processing layer"
  }
}

resource "google_monitoring_metric_descriptor" "reflex_activations" {
  count = var.nervous_system_enabled ? 1 : 0

  description  = "Number of reflex arc activations"
  display_name = "Reflex Activations"
  type         = "custom.googleapis.com/nervous_system/reflex_activations"
  metric_kind  = "CUMULATIVE"
  value_type   = "INT64"
  project      = var.project_id

  labels {
    key         = "neuron"
    value_type  = "STRING"
    description = "Neuron that fired"
  }

  labels {
    key         = "action"
    value_type  = "STRING"
    description = "Reflex action taken"
  }
}

# =============================================================================
# OUTPUTS
# =============================================================================

output "nervous_system_service_account" {
  description = "Nervous System service account email"
  value       = var.nervous_system_enabled ? google_service_account.nervous_system[0].email : null
}

output "nervous_system_events_topic" {
  description = "Pub/Sub topic for nervous system events"
  value       = var.nervous_system_enabled ? google_pubsub_topic.nervous_system_events[0].id : null
}

output "nervous_system_alerts_topic" {
  description = "Pub/Sub topic for nervous system alerts"
  value       = var.nervous_system_enabled ? google_pubsub_topic.nervous_system_alerts[0].id : null
}

output "nervous_system_escalations_topic" {
  description = "Pub/Sub topic for human escalations"
  value       = var.nervous_system_enabled ? google_pubsub_topic.nervous_system_escalations[0].id : null
}
