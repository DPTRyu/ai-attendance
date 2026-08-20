variable "project_id" {
  default = "ai-attendance-dev"
}

variable "region" {
  default = "asia-northeast1"
}

variable "api_image_tag" {
  type    = string
  default = "latest"
}

variable "mcp_image_tag" {
  type    = string
  default = "latest"
}