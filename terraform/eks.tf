# EKS Cluster Configuration

# VPC for EKS
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "${var.project_name}-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  enable_vpn_gateway = false
  enable_dns_hostnames = true
  enable_dns_support = true

  tags = merge(var.tags, {
    Name = "${var.project_name}-vpc"
    "kubernetes.io/cluster/${var.eks_cluster_name}" = "shared"
  })

  public_subnet_tags = {
    "kubernetes.io/cluster/${var.eks_cluster_name}" = "shared"
    "kubernetes.io/role/elb" = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/cluster/${var.eks_cluster_name}" = "shared"
    "kubernetes.io/role/internal-elb" = "1"
  }
}

# EKS Cluster
module "eks" {
  source = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = var.eks_cluster_name
  cluster_version = "1.31"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # Cluster access configuration
  cluster_endpoint_public_access  = true
  cluster_endpoint_private_access = true
  cluster_endpoint_public_access_cidrs = ["0.0.0.0/0"]

  # EKS Managed Node Groups
  eks_managed_node_groups = {
    main = {
      name = "trade-nodes"

      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"

      min_size     = 1
      max_size     = 3
      desired_size = 2

      disk_size = 50
      disk_type = "gp3"

      labels = {
        Environment = var.environment
        Application = var.project_name
      }

      tags = merge(var.tags, {
        Name = "trade-node-group"
      })
    }
  }

  # Cluster add-ons
  cluster_addons = {
    coredns                = {}
    eks-pod-identity-agent = {}
    kube-proxy            = {}
    vpc-cni               = {}
    aws-ebs-csi-driver    = {}
  }

  # Enable cluster creator admin permissions
  enable_cluster_creator_admin_permissions = true

  tags = merge(var.tags, {
    Name = var.eks_cluster_name
  })
}

# Output cluster information
output "cluster_endpoint" {
  description = "Endpoint for EKS control plane"
  value       = module.eks.cluster_endpoint
}

output "cluster_security_group_id" {
  description = "Security group ids attached to the cluster control plane"
  value       = module.eks.cluster_security_group_id
}

output "cluster_iam_role_name" {
  description = "IAM role name associated with EKS cluster"
  value       = module.eks.cluster_iam_role_name
}

output "cluster_certificate_authority_data" {
  description = "Base64 encoded certificate data required to communicate with the cluster"
  value       = module.eks.cluster_certificate_authority_data
}

output "cluster_name" {
  description = "The name of the EKS cluster"
  value       = module.eks.cluster_name
}