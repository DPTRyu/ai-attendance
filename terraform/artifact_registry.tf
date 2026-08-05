resource "google_artifact_registry_repository" "attendance" {
  repository_id = "ai-attendance"

  location = var.region

  format = "DOCKER"

  description = "AI Attendance Docker Repository"
}