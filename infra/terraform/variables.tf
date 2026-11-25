variable "project_name" {
  description = "Project identifier used for tagging and resource naming"
  type        = string
  default     = "pulsetrack"
}

variable "environment" {
  description = "Deployment environment (staging or production)"
  type        = string
  default     = "production"
}

variable "aws_region" {
  description = "AWS region for infrastructure provisioning"
  type        = string
  default     = "ap-south-1"
}

variable "vpc_cidr" {
  description = "CIDR block for the platform VPC"
  type        = string
  default     = "10.20.0.0/16"
}

variable "node_instance_type" {
  description = "EC2 instance type for EKS worker nodes"
  type        = string
  default     = "t3.medium"
}

variable "desired_node_count" {
  description = "Desired number of Kubernetes worker nodes"
  type        = number
  default     = 2
}
