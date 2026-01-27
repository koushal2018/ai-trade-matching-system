terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "trade-matching-terraform-state"
    key            = "frontend/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment     = var.environment
      Project         = "trade-matching-system"
      Component       = "frontend"
      ManagedBy       = "terraform"
      applicationName = "OTC_Agent"
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}
