param([string]$Region = "us-east-1")

$ErrorActionPreference = "Stop"

function Assert-Aws([string]$Step) {
    if ($LASTEXITCODE -ne 0) { throw "Falha em: $Step" }
}

function Set-PlainSecret([string]$Name, [string]$Value) {
    & aws secretsmanager describe-secret --secret-id $Name --region $Region *> $null
    if ($LASTEXITCODE -eq 0) {
        $arn = & aws secretsmanager put-secret-value --secret-id $Name --secret-string $Value --query ARN --output text --region $Region
    } else {
        $arn = & aws secretsmanager create-secret --name $Name --secret-string $Value --query ARN --output text --region $Region
    }
    Assert-Aws "salvar secret $Name"
    return $arn.Trim()
}

Write-Host "[1/8] Descobrindo conta e rede..." -ForegroundColor Cyan
$AccountId = (& aws sts get-caller-identity --query Account --output text --region $Region).Trim()
Assert-Aws "identificar conta AWS"
$LabRoleArn = (& aws iam get-role --role-name LabRole --query Role.Arn --output text).Trim()
Assert-Aws "obter LabRole"
$VpcId = (& aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text --region $Region).Trim()
$EcsSg = (& aws ec2 describe-security-groups --filters "Name=vpc-id,Values=$VpcId" "Name=group-name,Values=cloudtask-ecs-sg" --query "SecurityGroups[0].GroupId" --output text --region $Region).Trim()
Assert-Aws "localizar security group do ECS"

Write-Host "[2/8] Lendo endpoint e senha do RDS..." -ForegroundColor Cyan
$RdsEndpoint = (& aws rds describe-db-instances --db-instance-identifier cloudtask-db --query "DBInstances[0].Endpoint.Address" --output text --region $Region).Trim()
Assert-Aws "obter endpoint do RDS"
$DbPassword = (& aws secretsmanager get-secret-value --secret-id cloudtask/rds-password --query SecretString --output text --region $Region).Trim()
Assert-Aws "ler senha do RDS"
$DatabaseUrl = "postgresql+psycopg2://cloudtask:$DbPassword@${RdsEndpoint}:5432/cloudtask"

Write-Host "[3/8] Atualizando secrets da aplicacao..." -ForegroundColor Cyan
$DatabaseUrlSecretArn = Set-PlainSecret "cloudtask/database-url" $DatabaseUrl
$SecretKey = -join (((48..57) + (65..90) + (97..122)) | Get-Random -Count 32 | ForEach-Object { [char]$_ })
$SecretKeyArn = Set-PlainSecret "cloudtask/secret-key" $SecretKey

Write-Host "[4/8] Preparando bucket S3 privado..." -ForegroundColor Cyan
$BucketName = "cloudtask-uploads-$AccountId"
& aws s3api head-bucket --bucket $BucketName --region $Region *> $null
if ($LASTEXITCODE -ne 0) {
    & aws s3api create-bucket --bucket $BucketName --region $Region | Out-Null
    Assert-Aws "criar bucket S3"
}
& aws s3api put-public-access-block --bucket $BucketName --public-access-block-configuration "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true" --region $Region
Assert-Aws "bloquear acesso publico ao S3"

Write-Host "[5/8] Preparando logs e cluster ECS..." -ForegroundColor Cyan
& aws logs create-log-group --log-group-name /ecs/cloudtask-api --region $Region 2>$null
& aws ecs create-cluster --cluster-name cloudtask-cluster --region $Region | Out-Null
Assert-Aws "criar cluster ECS"

Write-Host "[6/8] Registrando task definition..." -ForegroundColor Cyan
$EcrImage = "$AccountId.dkr.ecr.$Region.amazonaws.com/cloudtask-api:latest"
$TaskDefinition = @{
    family = "cloudtask-api"
    networkMode = "awsvpc"
    requiresCompatibilities = @("FARGATE")
    cpu = "256"
    memory = "512"
    executionRoleArn = $LabRoleArn
    taskRoleArn = $LabRoleArn
    containerDefinitions = @(
        @{
            name = "api"
            image = $EcrImage
            essential = $true
            portMappings = @(@{ containerPort = 8000; hostPort = 8000; protocol = "tcp" })
            environment = @(
                @{ name = "APP_ENV"; value = "production" },
                @{ name = "APP_PORT"; value = "8000" },
                @{ name = "LOG_LEVEL"; value = "INFO" },
                @{ name = "STORAGE_MODE"; value = "s3" },
                @{ name = "AWS_REGION"; value = $Region },
                @{ name = "S3_BUCKET_NAME"; value = $BucketName },
                @{ name = "S3_PRESIGNED_URL_EXPIRES"; value = "3600" },
                @{ name = "FORCE_HTTPS"; value = "false" },
                @{ name = "TRUSTED_HOSTS"; value = "*" }
            )
            secrets = @(
                @{ name = "DATABASE_URL"; valueFrom = $DatabaseUrlSecretArn },
                @{ name = "SECRET_KEY"; valueFrom = $SecretKeyArn }
            )
            logConfiguration = @{
                logDriver = "awslogs"
                options = @{
                    "awslogs-group" = "/ecs/cloudtask-api"
                    "awslogs-region" = $Region
                    "awslogs-stream-prefix" = "ecs"
                }
            }
        }
    )
}
$TaskFile = Join-Path $env:TEMP "cloudtask-task-definition.json"
$TaskDefinition | ConvertTo-Json -Depth 20 | Set-Content -Path $TaskFile -Encoding utf8
$TaskArn = (& aws ecs register-task-definition --cli-input-json "file://$TaskFile" --query "taskDefinition.taskDefinitionArn" --output text --region $Region).Trim()
Assert-Aws "registrar task definition"

Write-Host "[7/8] Criando ou atualizando servico Fargate..." -ForegroundColor Cyan
$SubnetIds = @((& aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VpcId" "Name=map-public-ip-on-launch,Values=true" --query "Subnets[].SubnetId" --output text --region $Region) -split "\s+" | Where-Object { $_ })
if ($SubnetIds.Count -eq 0) { throw "Nenhuma subnet publica encontrada na VPC default." }
$NetworkConfiguration = @{ awsvpcConfiguration = @{ subnets = $SubnetIds; securityGroups = @($EcsSg); assignPublicIp = "ENABLED" } } | ConvertTo-Json -Depth 5 -Compress
$ServiceStatus = (& aws ecs describe-services --cluster cloudtask-cluster --services cloudtask-service --query "services[0].status" --output text --region $Region 2>$null).Trim()
if ($ServiceStatus -eq "ACTIVE") {
    & aws ecs update-service --cluster cloudtask-cluster --service cloudtask-service --task-definition $TaskArn --desired-count 1 --network-configuration $NetworkConfiguration --force-new-deployment --region $Region | Out-Null
    Assert-Aws "atualizar servico ECS"
} else {
    & aws ecs create-service --cluster cloudtask-cluster --service-name cloudtask-service --task-definition $TaskArn --desired-count 1 --launch-type FARGATE --platform-version LATEST --network-configuration $NetworkConfiguration --region $Region | Out-Null
    Assert-Aws "criar servico ECS"
}

Write-Host "[8/8] Aguardando o servico estabilizar (pode levar alguns minutos)..." -ForegroundColor Cyan
& aws ecs wait services-stable --cluster cloudtask-cluster --services cloudtask-service --region $Region
Assert-Aws "aguardar estabilidade do ECS"

$Task = (& aws ecs list-tasks --cluster cloudtask-cluster --service-name cloudtask-service --desired-status RUNNING --query "taskArns[0]" --output text --region $Region).Trim()
$Eni = (& aws ecs describe-tasks --cluster cloudtask-cluster --tasks $Task --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value | [0]" --output text --region $Region).Trim()
$PublicIp = (& aws ec2 describe-network-interfaces --network-interface-ids $Eni --query "NetworkInterfaces[0].Association.PublicIp" --output text --region $Region).Trim()

Write-Host ""
Write-Host "DEPLOY CONCLUIDO" -ForegroundColor Green
Write-Host "RDS: $RdsEndpoint"
Write-Host "S3:  $BucketName"
Write-Host "API: http://${PublicIp}:8000"
Write-Host "Health: http://${PublicIp}:8000/health"
Write-Host "Ready:  http://${PublicIp}:8000/health/ready"
