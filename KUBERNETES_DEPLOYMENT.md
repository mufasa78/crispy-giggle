# Kubernetes Deployment Instructions

This document provides instructions for deploying the application using Kubernetes.

## Prerequisites

- Kubernetes cluster (local or cloud-based)
- kubectl installed and configured
- Docker installed (for building the image)
- Docker registry access (if deploying to a remote cluster)

## Deployment Steps

### 1. Build and Push the Docker Image

First, build the Docker image:

```bash
docker build -t shopee-scraper-api:latest .
```

If you're using a remote Kubernetes cluster, you'll need to tag and push the image to a registry:

```bash
# Tag the image
docker tag shopee-scraper-api:latest your-registry/shopee-scraper-api:latest

# Push the image
docker push your-registry/shopee-scraper-api:latest
```

Then update the image name in `k8s/deployment.yaml` to match your registry:

```yaml
image: your-registry/shopee-scraper-api:latest
```

### 2. Configure Secrets and ConfigMaps

Before deploying, update the secrets in `k8s/secret.yaml`:

```bash
# Edit the secret file to update sensitive information
nano k8s/secret.yaml
```

Make sure to replace the placeholder values with secure credentials:
- `database-url`: Your PostgreSQL connection string
- `session-secret`: A secure random string for session encryption
- `postgres-user`: PostgreSQL username
- `postgres-password`: PostgreSQL password

Also, update the ConfigMap in `k8s/configmap.yaml` if needed:

```bash
# Edit the ConfigMap file
nano k8s/configmap.yaml
```

### 3. Deploy the PostgreSQL Database

Deploy the PostgreSQL components:

```bash
# Create the persistent volume claim
kubectl apply -f k8s/postgres-pvc.yaml

# Deploy PostgreSQL
kubectl apply -f k8s/postgres-deployment.yaml
kubectl apply -f k8s/postgres-service.yaml
```

### 4. Deploy the Application

Deploy the application components:

```bash
# Create ConfigMap and Secret
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml

# Deploy the application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### 5. Deploy the Ingress (Optional)

If you need external access to your application:

```bash
kubectl apply -f k8s/ingress.yaml
```

Make sure to update the host in `k8s/ingress.yaml` to match your domain.

### 6. Verify the Deployment

Check if all pods are running:

```bash
kubectl get pods
```

Check the services:

```bash
kubectl get services
```

### 7. Access the Application

If you're using Ingress, access the application at your configured domain.

If you're using a local Kubernetes cluster (like Minikube), you can port-forward to access the application:

```bash
kubectl port-forward service/shopee-scraper-api 8080:80
```

Then access the application at http://localhost:8080

### 8. Create an Admin User

Visit the following URL to create an admin user:

```
http://your-domain/setup-admin
```

Or if using port-forwarding:

```
http://localhost:8080/setup-admin
```

## Scaling the Application

To scale the application, you can modify the number of replicas:

```bash
kubectl scale deployment shopee-scraper-api --replicas=3
```

## Monitoring and Logs

To view logs for the application:

```bash
kubectl logs -l app=shopee-scraper-api
```

To view logs for the database:

```bash
kubectl logs -l app=postgres
```

## Troubleshooting

### Database Connection Issues

If the application cannot connect to the database, check:

1. The database pod is running:
   ```bash
   kubectl get pods -l app=postgres
   ```

2. The database service is working:
   ```bash
   kubectl describe service postgres
   ```

3. The secret containing the database URL is correctly mounted:
   ```bash
   kubectl describe pods -l app=shopee-scraper-api
   ```

### Application Issues

If the application is not working correctly:

1. Check the application logs:
   ```bash
   kubectl logs -l app=shopee-scraper-api
   ```

2. Check the application pod status:
   ```bash
   kubectl describe pods -l app=shopee-scraper-api
   ```

## Updating the Application

To update the application with a new version:

1. Build and push a new Docker image with a new tag:
   ```bash
   docker build -t your-registry/shopee-scraper-api:v2 .
   docker push your-registry/shopee-scraper-api:v2
   ```

2. Update the deployment to use the new image:
   ```bash
   kubectl set image deployment/shopee-scraper-api shopee-scraper-api=your-registry/shopee-scraper-api:v2
   ```

## Cleaning Up

To remove all resources:

```bash
kubectl delete -f k8s/
```

This will delete all resources defined in the Kubernetes YAML files.
