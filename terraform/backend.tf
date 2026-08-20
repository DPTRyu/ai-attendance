terraform {
  backend "gcs" {
    bucket = "ai-attendance-tfstate-706964629489"
    prefix = "ai-attendance"
  }
}