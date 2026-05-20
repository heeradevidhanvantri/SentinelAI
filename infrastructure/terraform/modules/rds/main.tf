variable "environment" { type = string }
variable "vpc_id" { type = string }
variable "subnet_ids" { type = list(string) }

output "endpoint" { value = "sentinelai-${var.environment}.region.rds.amazonaws.com" }
