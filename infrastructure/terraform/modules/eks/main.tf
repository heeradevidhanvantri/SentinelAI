# EKS cluster module stub - extend for production
variable "environment" { type = string }
variable "vpc_id" { type = string }
variable "private_subnets" { type = list(string) }
variable "cluster_name" { type = string }

output "cluster_endpoint" { value = "https://eks.${var.environment}.sentinelai.local" }
