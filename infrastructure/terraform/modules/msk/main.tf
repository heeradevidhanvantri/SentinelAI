variable "environment" { type = string }
variable "vpc_id" { type = string }
variable "subnet_ids" { type = list(string) }

output "bootstrap_brokers" { value = "b-1.sentinelai.${var.environment}.kafka.amazonaws.com:9092" }
