# Weather API - AWS Infrastructure

This directory contains Terraform modules for deploying the Weather Data Engineering API on AWS.

## 🏗️ Architecture

The infrastructure consists of the following components:

- **VPC**: Multi-AZ networking with public and private subnets
- **RDS PostgreSQL**: Database for weather data storage
- **ECS Fargate**: Container orchestration for the API
- **Application Load Balancer**: Load balancing and SSL termination
- **S3**: Object storage for data files and backups
- **CloudWatch**: Monitoring, logging, and alerting
- **ECR**: Container registry for Docker images

## 🚀 Quick Start

### Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** >= 1.0 installed
3. Appropriate AWS IAM permissions

### Deployment

1. **Clone and navigate to terraform directory**:
   ```bash
   cd terraform
   ```

2. **Copy and customize configuration**:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your specific values
   ```

3. **Initialize Terraform**:
   ```bash
   terraform init
   ```

4. **Plan deployment**:
   ```bash
   terraform plan
   ```

5. **Apply infrastructure**:
   ```bash
   terraform apply
   ```

### Configuration

Edit `terraform.tfvars` with your specific values:

```hcl
# Required variables
aws_region = "us-west-2"
project_name = "weather-api"
environment = "dev"
db_password = "your-secure-password"  # pragma: allowlist secret

# Optional customization
vpc_cidr = "10.0.0.0/16"
db_instance_class = "db.t3.micro"
ecs_desired_count = 2
```

## 📋 Modules

### VPC Module (`modules/vpc/`)
- Creates VPC with public and private subnets across multiple AZs
- Sets up NAT gateways for private subnet internet access
- Configures route tables and VPC flow logs

### Security Module (`modules/security/`)
- Defines security groups for ALB, ECS, and RDS
- Implements least-privilege access patterns
- Configures VPC endpoint security

### RDS Module (`modules/rds/`)
- PostgreSQL database with automated backups
- Parameter groups for performance optimization
- Enhanced monitoring and Performance Insights
- Encryption at rest and in transit

### ECS Module (`modules/ecs/`)
- Fargate cluster for serverless containers
- Auto-scaling task definitions
- CloudWatch logging integration
- IAM roles for task execution

### ALB Module (`modules/alb/`)
- Application Load Balancer with health checks
- Target groups for ECS services
- Optional SSL/TLS termination
- HTTP to HTTPS redirect

### S3 Module (`modules/s3/`)
- Data storage buckets with versioning
- Lifecycle policies for cost optimization
- Server-side encryption
- Access logging

### CloudWatch Module (`modules/cloudwatch/`)
- Application and infrastructure monitoring
- Custom metrics and alarms
- Log aggregation and retention
- Operational dashboards

### ECR Module (`modules/ecr/`)
- Container registry for Docker images
- Image scanning and lifecycle policies
- Repository access controls

## 🔧 Usage Examples

### Development Environment
```bash
# Deploy with minimal resources
terraform apply -var="environment=dev" -var="db_instance_class=db.t3.micro"
```

### Production Environment
```bash
# Deploy with production-ready configuration
terraform apply -var="environment=prod" -var="db_instance_class=db.r5.large" -var="ecs_desired_count=5"
```

### Custom Domain Setup
```bash
# Deploy with SSL certificate
terraform apply -var="ssl_certificate_arn=arn:aws:acm:us-west-2:123456789012:certificate/12345678-1234-1234-1234-123456789012"
```

## 🔒 Security Features

- **Network Isolation**: Private subnets for database and application
- **Encryption**: At rest and in transit for all data
- **Access Control**: IAM roles and security groups
- **Monitoring**: CloudWatch and VPC Flow Logs
- **Secrets Management**: Sensitive data marked as sensitive

## 💰 Cost Optimization

- **Right-sizing**: T3 instances for development, larger for production
- **Storage Lifecycle**: Automated S3 transitions to cheaper storage classes
- **Monitoring**: CloudWatch alarms to prevent unexpected costs
- **Spot Instances**: Can be configured for non-critical workloads

## 📊 Monitoring

### CloudWatch Dashboards
- Application performance metrics
- Infrastructure health monitoring
- Cost and usage tracking

### Alarms
- High CPU/memory utilization
- Database connection issues
- Application error rates
- Storage capacity warnings

## 🛠️ Maintenance

### Regular Tasks
- **Updates**: Keep Terraform and providers updated
- **Backups**: Automated RDS backups and S3 versioning
- **Monitoring**: Review CloudWatch metrics and logs
- **Security**: Update security groups and IAM policies

### Disaster Recovery
- **RDS**: Point-in-time recovery available
- **S3**: Cross-region replication can be enabled
- **ECS**: Multi-AZ deployment for high availability

## 🔧 Customization

### Adding New Services
1. Create new module in `modules/` directory
2. Add module call in `main.tf`
3. Update variables and outputs as needed

### Multi-Environment Support
```bash
# Use workspaces for multiple environments
terraform workspace new staging
terraform workspace new production
```

### Advanced Configuration
- **Auto Scaling**: Configure ECS service auto-scaling
- **CDN**: Add CloudFront distribution
- **WAF**: Add Web Application Firewall
- **Route53**: Add DNS management

## 📋 Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `aws_region` | AWS region | `us-west-2` | No |
| `project_name` | Project name | `weather-api` | No |
| `environment` | Environment name | `dev` | No |
| `vpc_cidr` | VPC CIDR block | `10.0.0.0/16` | No |
| `db_password` | Database password | - | **Yes** |
| `container_image` | Container image | `nginx:latest` | No |

## 🔗 Outputs

| Output | Description |
|--------|-------------|
| `application_url` | Application URL |
| `rds_endpoint` | Database endpoint |
| `ecr_repository_url` | Container registry URL |
| `s3_bucket_name` | Data storage bucket |

## 🆘 Troubleshooting

### Common Issues

**Terraform State Lock**
```bash
# Force unlock if needed
terraform force-unlock LOCK_ID
```

**Resource Conflicts**
```bash
# Import existing resources
terraform import aws_s3_bucket.example bucket-name
```

**Permission Errors**
- Ensure AWS credentials have required permissions
- Check IAM policies and roles

### Support
- Review AWS CloudWatch logs
- Check Terraform state file
- Validate configuration with `terraform validate`

---

*For more information, see the main project README.md*
