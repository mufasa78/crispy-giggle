# Troubleshooting Guide

This document provides solutions for common issues you might encounter when deploying and running the application.

## Table of Contents

- [Docker Deployment Issues](#docker-deployment-issues)
- [Kubernetes Deployment Issues](#kubernetes-deployment-issues)
- [External Access Issues](#external-access-issues)
- [Database Issues](#database-issues)
- [Application Issues](#application-issues)

## Docker Deployment Issues

### Container Not Starting

**Symptoms:**
- Docker Compose shows errors when starting containers
- Containers exit immediately after starting

**Solutions:**

1. Check the logs:
   ```bash
   docker-compose logs
   ```

2. Check if ports are already in use:
   ```bash
   netstat -ano | findstr :5000
   ```

3. Make sure all required files are present:
   ```bash
   ls -la
   ```

4. Try rebuilding the containers:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

### Image Build Failures

**Symptoms:**
- Docker build fails with errors
- Docker Compose shows build errors

**Solutions:**

1. Check if you have enough disk space:
   ```bash
   df -h
   ```

2. Make sure your Dockerfile is correct:
   ```bash
   cat Dockerfile
   ```

3. Try cleaning Docker cache:
   ```bash
   docker system prune -a
   ```

4. Check if all required files are included in the build context:
   ```bash
   ls -la
   ```

## Kubernetes Deployment Issues

### Pods Not Starting

**Symptoms:**
- Pods show status "Pending" or "CrashLoopBackOff"
- Pods restart repeatedly

**Solutions:**

1. Check pod status:
   ```bash
   kubectl get pods
   ```

2. Check pod details:
   ```bash
   kubectl describe pod <pod-name>
   ```

3. Check pod logs:
   ```bash
   kubectl logs <pod-name>
   ```

4. Check if the cluster has enough resources:
   ```bash
   kubectl describe nodes
   ```

### Service Not Accessible

**Symptoms:**
- Cannot access the application via service
- Service shows no endpoints

**Solutions:**

1. Check service status:
   ```bash
   kubectl get services
   ```

2. Check service details:
   ```bash
   kubectl describe service shopee-scraper-api
   ```

3. Check if pods are running and ready:
   ```bash
   kubectl get pods -l app=shopee-scraper-api
   ```

4. Try port-forwarding to test direct access:
   ```bash
   kubectl port-forward service/shopee-scraper-api 8080:80
   ```

### Ingress Not Working

**Symptoms:**
- Cannot access the application via domain
- Ingress shows no backends

**Solutions:**

1. Check ingress status:
   ```bash
   kubectl get ingress
   ```

2. Check ingress details:
   ```bash
   kubectl describe ingress shopee-scraper-ingress
   ```

3. Check if ingress controller is running:
   ```bash
   kubectl get pods -n ingress-nginx
   ```

4. Check ingress controller logs:
   ```bash
   kubectl logs -n ingress-nginx <ingress-controller-pod>
   ```

## External Access Issues

### Nginx Not Working

**Symptoms:**
- Cannot access the application via Nginx
- Nginx shows errors

**Solutions:**

1. Check if Nginx is running:
   ```bash
   docker-compose -f docker-compose.nginx.yml ps
   ```

2. Check Nginx logs:
   ```bash
   docker-compose -f docker-compose.nginx.yml logs
   ```

3. Check Nginx configuration:
   ```bash
   cat nginx.conf
   ```

4. Make sure the application is running and accessible:
   ```bash
   curl http://localhost:5000
   ```

### Domain Not Resolving

**Symptoms:**
- Cannot access the application via domain
- Browser shows "This site can't be reached"

**Solutions:**

1. Check if the domain is in your hosts file:
   ```bash
   cat /etc/hosts  # Linux/Mac
   type C:\Windows\System32\drivers\etc\hosts  # Windows
   ```

2. Add the domain to your hosts file:
   ```
   127.0.0.1 shopee-scraper.example.com
   ```

3. Flush DNS cache:
   ```bash
   ipconfig /flushdns  # Windows
   sudo killall -HUP mDNSResponder  # Mac
   sudo systemd-resolve --flush-caches  # Linux
   ```

4. Check if the domain resolves:
   ```bash
   ping shopee-scraper.example.com
   ```

### SSL Certificate Issues

**Symptoms:**
- Browser shows "Your connection is not private"
- SSL certificate errors

**Solutions:**

1. Check if the SSL certificate is valid:
   ```bash
   certbot certificates
   ```

2. Renew the certificate:
   ```bash
   certbot renew
   ```

3. Check if the certificate files are correctly referenced in Nginx configuration:
   ```bash
   cat nginx.conf
   ```

4. Try using a self-signed certificate for testing:
   ```bash
   openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout key.pem -out cert.pem
   ```

## Database Issues

### Connection Failures

**Symptoms:**
- Application shows database connection errors
- Cannot connect to the database

**Solutions:**

1. Check if the database container is running:
   ```bash
   docker-compose ps db
   ```

2. Check database logs:
   ```bash
   docker-compose logs db
   ```

3. Make sure the DATABASE_URL is correct:
   ```bash
   cat docker-compose.yml
   ```

4. Try connecting to the database directly:
   ```bash
   docker exec -it project-db-1 psql -U postgres -d shopeescraper
   ```

### Data Persistence Issues

**Symptoms:**
- Data is lost after container restart
- Database is empty after restart

**Solutions:**

1. Check if the volume is correctly configured:
   ```bash
   docker volume ls
   ```

2. Check volume details:
   ```bash
   docker volume inspect postgres_data
   ```

3. Make sure the volume is mounted correctly:
   ```bash
   docker-compose ps db
   ```

4. Check if the data directory has correct permissions:
   ```bash
   docker exec -it project-db-1 ls -la /var/lib/postgresql/data
   ```

## Application Issues

### Application Not Starting

**Symptoms:**
- Application container exits immediately
- Application shows startup errors

**Solutions:**

1. Check application logs:
   ```bash
   docker-compose logs api
   ```

2. Make sure all environment variables are set:
   ```bash
   cat docker-compose.yml
   ```

3. Check if the application code is correct:
   ```bash
   cat main.py
   ```

4. Try running the application in debug mode:
   ```bash
   docker-compose run --rm api python main.py
   ```

### API Errors

**Symptoms:**
- API endpoints return errors
- API requests fail

**Solutions:**

1. Check application logs:
   ```bash
   docker-compose logs api
   ```

2. Make sure the database is accessible:
   ```bash
   docker-compose logs db
   ```

3. Check if the API is correctly configured:
   ```bash
   cat main.py
   ```

4. Try making a direct API request:
   ```bash
   curl http://localhost:5000/api/docs
   ```

### Admin Setup Issues

**Symptoms:**
- Cannot access the setup-admin page
- Admin user creation fails

**Solutions:**

1. Check if the application is running:
   ```bash
   docker-compose ps api
   ```

2. Check application logs:
   ```bash
   docker-compose logs api
   ```

3. Make sure the database is accessible:
   ```bash
   docker-compose logs db
   ```

4. Try accessing the setup-admin page directly:
   ```bash
   curl http://localhost:5000/setup-admin
   ```

## General Troubleshooting Steps

1. **Check Logs**: Always check the logs first to identify the issue.
2. **Restart Containers**: Sometimes a simple restart can fix issues.
3. **Check Configuration**: Make sure all configuration files are correct.
4. **Check Network**: Make sure all services can communicate with each other.
5. **Check Resources**: Make sure you have enough CPU, memory, and disk space.
6. **Check Permissions**: Make sure all files and directories have correct permissions.
7. **Check Versions**: Make sure you're using compatible versions of all components.
8. **Check Firewall**: Make sure the firewall is not blocking any required ports.
9. **Check DNS**: Make sure DNS resolution is working correctly.
10. **Check SSL**: Make sure SSL certificates are valid and correctly configured.
