variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "staging"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EKS node instance type"
  type        = string
  default     = "m5.xlarge"
}
