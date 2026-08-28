# GridMind OS — AWS Deployment Script
# Frontend: AWS Amplify | Backend: AWS App Runner (ECR)
$ErrorActionPreference = "Stop"
$Region = "us-east-1"
$AccountId = "120569623789"
$RepoName = "gridmind-api"
$ServiceName = "gridmind-api"
$AppName = "gridmind-os"

Write-Host "=== GridMind OS AWS Deployment ===" -ForegroundColor Cyan

# 1. Build & push Docker image to ECR
Write-Host "`n[1/4] Building Docker image..." -ForegroundColor Yellow
aws ecr describe-repositories --repository-names $RepoName --region $Region 2>$null
if ($LASTEXITCODE -ne 0) {
    aws ecr create-repository --repository-name $RepoName --region $Region
}

aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin "$AccountId.dkr.ecr.$Region.amazonaws.com"

docker build -t $RepoName:latest ./backend
docker tag "${RepoName}:latest" "${AccountId}.dkr.ecr.${Region}.amazonaws.com/${RepoName}:latest"
docker push "${AccountId}.dkr.ecr.${Region}.amazonaws.com/${RepoName}:latest"

# 2. Create or update App Runner service
Write-Host "`n[2/4] Deploying App Runner service..." -ForegroundColor Yellow
$ImageUri = "${AccountId}.dkr.ecr.${Region}.amazonaws.com/${RepoName}:latest"

$existing = aws apprunner list-services --region $Region --query "ServiceSummaryList[?ServiceName=='$ServiceName'].ServiceArn" --output text
if ($existing) {
    Write-Host "Updating existing App Runner service..."
    aws apprunner start-deployment --service-arn $existing --region $Region
} else {
    # Create IAM role for App Runner ECR access if needed
    $RoleArn = "arn:aws:iam::${AccountId}:role/AppRunnerECRAccessRole"
    
    @"
{
  "ServiceName": "$ServiceName",
  "SourceConfiguration": {
    "ImageRepository": {
      "ImageIdentifier": "$ImageUri",
      "ImageRepositoryType": "ECR",
      "ImageConfiguration": {
        "Port": "8000",
        "RuntimeEnvironmentVariables": {
          "SKIP_SIMULATOR": "1",
          "DATABASE_URL": "sqlite+aiosqlite:////tmp/gridmind.db"
        }
      }
    },
    "AutoDeploymentsEnabled": true,
    "AuthenticationConfiguration": {
      "AccessRoleArn": "$RoleArn"
    }
  },
  "InstanceConfiguration": {
    "Cpu": "1024",
    "Memory": "2048"
  },
  "HealthCheckConfiguration": {
    "Protocol": "HTTP",
    "Path": "/api/v1/health",
    "Interval": 10,
    "Timeout": 5,
    "HealthyThreshold": 1,
    "UnhealthyThreshold": 3
  }
}
"@ | Out-File -Encoding utf8 apprunner-config.json

    aws apprunner create-service --cli-input-json file://apprunner-config.json --region $Region
}

Write-Host "`n[3/4] Get App Runner URL (may take 2-3 min on first deploy)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30
$ApiUrl = aws apprunner list-services --region $Region --query "ServiceSummaryList[?ServiceName=='$ServiceName'].ServiceUrl" --output text
Write-Host "API URL: https://$ApiUrl" -ForegroundColor Green

# 3. Amplify frontend
Write-Host "`n[4/4] Amplify frontend — set env NEXT_PUBLIC_API_URL=https://$ApiUrl/api/v1" -ForegroundColor Yellow
Write-Host "Done! Configure Amplify app with GitHub repo and the API URL above." -ForegroundColor Cyan
