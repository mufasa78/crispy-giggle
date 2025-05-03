# Shopee Scraper Deployment Guide

This document provides comprehensive instructions for deploying the Shopee Scraper application using Docker, Docker Compose, and Kubernetes.

## Table of Contents

- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [External Access Setup](#external-access-setup)
- [Troubleshooting](#troubleshooting)

## Docker Deployment

### Prerequisites

- Docker installed on your system
- Docker Compose installed on your system

### Deployment Steps

1. **Clone the Repository**

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Configure Environment Variables**

   The docker-compose.yml file is already configured with default environment variables. You can modify them if needed.

3. **Build and Start the Containers**

   ```bash
   docker-compose up -d
   ```

   This will:
   - Build the Docker image for the application
   - Start the PostgreSQL database container
   - Start the application container
   - Connect the application to the database

4. **Access the Application**

   The application will be available at:

   ```
   http://localhost:5000
   ```

5. **Create an Admin User**

   Visit the following URL to create an admin user:

   ```
   http://localhost:5000/setup-admin
   ```

6. **Check Application Status**

   You can use the provided script to check the status of your application:

   ```powershell
   .\check-app-status.ps1
   ```

7. **Stop the Containers**

   To stop the containers:

   ```bash
   docker-compose down
   ```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster (local or cloud-based)
- kubectl installed and configured
- Docker installed (for building the image)
- Docker registry access (if deploying to a remote cluster)

### Deployment Steps

1. **Build and Push the Docker Image**

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

2. **Deploy to Kubernetes**

   You can use the provided script to deploy to Kubernetes:

   ```powershell
   .\deploy-kubernetes.ps1
   ```

   Or manually apply the Kubernetes configuration files:

   ```bash
   # Create ConfigMap and Secret
   kubectl apply -f k8s/configmap.yaml
   kubectl apply -f k8s/secret.yaml

   # Deploy PostgreSQL
   kubectl apply -f k8s/postgres-pvc.yaml
   kubectl apply -f k8s/postgres-deployment.yaml
   kubectl apply -f k8s/postgres-service.yaml

   # Deploy the application
   kubectl apply -f k8s/deployment.yaml
   kubectl apply -f k8s/service.yaml

   # Deploy Ingress (optional)
   kubectl apply -f k8s/ingress.yaml
   ```

3. **Access the Application**

   If you're using Ingress, access the application at your configured domain.

   If you're using a local Kubernetes cluster (like Minikube), you can port-forward to access the application:

   ```bash
   kubectl port-forward service/shopee-scraper-api 8080:80
   ```

   Then access the application at http://localhost:8080

4. **Create an Admin User**

   Visit the following URL to create an admin user:

   ```
   http://your-domain/setup-admin
   ```

   Or if using port-forwarding:

   ```
   http://localhost:8080/setup-admin
   ```

## External Access Setup

For setting up external access to your application, refer to the [EXTERNAL_ACCESS.md](EXTERNAL_ACCESS.md) document.

You can also use the provided script to set up external access with Nginx:

```powershell
.\setup-external-access.ps1
```

## Troubleshooting

### Docker Deployment Issues

1. **Container not starting**

   Check the logs:

   ```bash
   docker-compose logs
   ```

2. **Database connection issues**

   Make sure the DATABASE_URL environment variable is correctly set in docker-compose.yml.

3. **Port conflicts**

   If port 5000 is already in use, change the port mapping in docker-compose.yml:

   ```yaml
   ports:
     - "8080:5000"  # Map port 8080 on the host to port 5000 in the container
   ```

### Kubernetes Deployment Issues

1. **Pods not starting**

   Check the pod status and logs:

   ```bash
   kubectl get pods
   kubectl describe pod <pod-name>
   kubectl logs <pod-name>
   ```

2. **Service not accessible**

   Check the service status:

   ```bash
   kubectl get services
   kubectl describe service shopee-scraper-api
   ```

3. **Ingress not working**

   Check the ingress status:

   ```bash
   kubectl get ingress
   kubectl describe ingress shopee-scraper-ingress
   ```

### External Access Issues

1. **Nginx not working**

   Check the Nginx logs:

   ```bash
   docker-compose -f docker-compose.nginx.yml logs
   ```

2. **Domain not resolving**

   Make sure your hosts file is correctly configured or your DNS settings are correct.

3. **SSL certificate issues**

   Check the SSL certificate status:

   ```bash
   certbot certificates
   ```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
