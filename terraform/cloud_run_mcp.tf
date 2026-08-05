resource "google_cloud_run_v2_service" "attendance_mcp" {
  name     = "attendance-mcp"
  location = var.region

  template {
    containers {
      image = "asia-northeast1-docker.pkg.dev/${var.project_id}/ai-attendance/attendance-mcp:latest"

      ports {
        container_port = 8080
      }

      env {
        name  = "ATTENDANCE_API_URL"
        value = "https://attendance-api-706964629489.asia-northeast1.run.app/api/v1"
      }
    }
  }

  deletion_protection = false
}