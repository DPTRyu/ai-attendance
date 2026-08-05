resource "google_cloud_run_v2_service_iam_member" "public_access" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.attendance_api.name

  role = "roles/run.invoker"

  member = "allUsers"
}