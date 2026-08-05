resource "google_cloud_run_v2_service" "attendance_api" {
  name     = "attendance-api"
  location = var.region

  template {
    containers {
      image = "asia-northeast1-docker.pkg.dev/${var.project_id}/ai-attendance/attendance-api:latest"

      ports {
        container_port = 8080
      }
    }
  }

  deletion_protection = false
}