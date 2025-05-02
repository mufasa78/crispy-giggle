# Docker Deployment Instructions

This document provides instructions for deploying the application using Docker.

## Prerequisites

- Docker installed on your system
- Docker Compose installed on your system

## Deployment Steps

### 1. Clone the Repository

```bash
git clone <repository-url>
cd <repository-directory>
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory with the following variables:

```
# Database URL for PostgreSQL
DATABASE_URL=postgresql://postgres:postgres@db:5432/shopeescraper

# Session secret for Flask
SESSION_SECRET=your-secret-key-here

# Port for the application
PORT=5000
```

Make sure to replace `your-secret-key-here` with a secure random string.

### 3. Build and Start the Containers

```bash
docker-compose up -d
```

This will:
- Build the Docker image for the application
- Start the PostgreSQL database container
- Start the application container
- Connect the application to the database

### 4. Access the Application

The application will be available at:

```
http://localhost:5000
```

### 5. Create an Admin User

Visit the following URL to create an admin user:

```
http://localhost:5000/setup-admin
```

### 6. Stop the Containers

To stop the containers:

```bash
docker-compose down
```

## Troubleshooting

### Database Connection Issues

If the application cannot connect to the database, make sure:

1. The database container is running:
   ```bash
   docker-compose ps
   ```

2. The `DATABASE_URL` in the `.env` file is correct:
   ```
   DATABASE_URL=postgresql://postgres:postgres@db:5432/shopeescraper
   ```

### Application Logs

To view the application logs:

```bash
docker-compose logs api
```

To view the database logs:

```bash
docker-compose logs db
```

## Data Persistence

The PostgreSQL data is stored in a Docker volume named `postgres_data`. This ensures that your data persists even if the containers are stopped or removed.

## Scaling

To scale the application for production use:

1. Modify the `docker-compose.yml` file to increase the number of workers:
   ```yaml
   CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers=4", "main:app"]
   ```

2. Consider using a production-grade database setup with proper backups and monitoring.
