output "vpc_id" {
  description = "Provisioned VPC ID"
  value       = aws_vpc.platform.id
}

output "private_subnet_ids" {
  description = "Private subnet IDs for Kubernetes worker nodes"
  value       = aws_subnet.private[*].id
}

output "ecr_repository_url" {
  description = "Container registry URL for PulseTrack images"
  value       = aws_ecr_repository.app.repository_url
}
