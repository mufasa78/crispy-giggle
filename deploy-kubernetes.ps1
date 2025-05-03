# Kubernetes Deployment Script for Windows PowerShell

# Build the Docker image
Write-Host "Building Docker image..." -ForegroundColor Green
docker build -t shopee-scraper-api:latest .

# Check if the user wants to push to a registry
$pushToRegistry = Read-Host "Do you want to push to a Docker registry? (y/n)"
if ($pushToRegistry -eq "y") {
    $registry = Read-Host "Enter your Docker registry URL (e.g., docker.io/username)"
    
    # Tag the image
    Write-Host "Tagging image for registry: $registry" -ForegroundColor Green
    docker tag shopee-scraper-api:latest $registry/shopee-scraper-api:latest
    
    # Push the image
    Write-Host "Pushing image to registry..." -ForegroundColor Green
    docker push $registry/shopee-scraper-api:latest
    
    # Update the deployment file
    Write-Host "Updating deployment file with registry image..." -ForegroundColor Green
    (Get-Content -Path k8s/deployment.yaml) -replace 'image: shopee-scraper-api:latest', "image: $registry/shopee-scraper-api:latest" | Set-Content -Path k8s/deployment.yaml
}

# Deploy to Kubernetes
Write-Host "Deploying to Kubernetes..." -ForegroundColor Green

# Create namespace if it doesn't exist
$namespace = Read-Host "Enter Kubernetes namespace (leave blank for default)"
if ($namespace) {
    kubectl create namespace $namespace --dry-run=client -o yaml | kubectl apply -f -
    $namespaceArg = "-n $namespace"
} else {
    $namespaceArg = ""
}

# Apply ConfigMap and Secret
Write-Host "Applying ConfigMap and Secret..." -ForegroundColor Green
kubectl apply -f k8s/configmap.yaml $namespaceArg
kubectl apply -f k8s/secret.yaml $namespaceArg

# Deploy PostgreSQL
Write-Host "Deploying PostgreSQL..." -ForegroundColor Green
kubectl apply -f k8s/postgres-pvc.yaml $namespaceArg
kubectl apply -f k8s/postgres-deployment.yaml $namespaceArg
kubectl apply -f k8s/postgres-service.yaml $namespaceArg

# Wait for PostgreSQL to be ready
Write-Host "Waiting for PostgreSQL to be ready..." -ForegroundColor Yellow
kubectl wait --for=condition=available --timeout=60s deployment/postgres $namespaceArg

# Deploy the application
Write-Host "Deploying the application..." -ForegroundColor Green
kubectl apply -f k8s/deployment.yaml $namespaceArg
kubectl apply -f k8s/service.yaml $namespaceArg

# Ask if ingress should be deployed
$deployIngress = Read-Host "Do you want to deploy an Ingress resource? (y/n)"
if ($deployIngress -eq "y") {
    $domain = Read-Host "Enter your domain name (e.g., shopee-scraper.example.com)"
    
    # Update the ingress file with the domain
    Write-Host "Updating ingress file with domain: $domain" -ForegroundColor Green
    (Get-Content -Path k8s/ingress.yaml) -replace 'host: shopee-scraper.example.com', "host: $domain" | Set-Content -Path k8s/ingress.yaml
    
    # Apply the ingress
    kubectl apply -f k8s/ingress.yaml $namespaceArg
}

# Check deployment status
Write-Host "Checking deployment status..." -ForegroundColor Green
kubectl get pods $namespaceArg
kubectl get services $namespaceArg

if ($deployIngress -eq "y") {
    kubectl get ingress $namespaceArg
}

Write-Host "Deployment completed!" -ForegroundColor Green
Write-Host "For more information, please refer to KUBERNETES_DEPLOYMENT.md" -ForegroundColor Cyan
