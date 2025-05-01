# Shopee Data API - Deployment Guide

## Overview

This guide explains how to deploy the Shopee Data API to Render.com, which will host both the backend API and frontend interface in a single platform. Render.com offers a generous free tier that is sufficient for small to medium-scale usage.

## Why Render.com?

- **Free Tier**: Generous free tier with 750 hours of runtime per month
- **Full-Stack**: Can host both the API backend and web frontend
- **PostgreSQL**: Includes a free PostgreSQL database
- **Automated Deployment**: Connects to GitHub for continuous deployment
- **Environment Variables**: Secure management of secrets and configuration
- **Blueprint Deployments**: Allows setting up the entire stack in one go using the `render.yaml` file

## Deployment Steps

### 1. Prepare Your Repository

1. Push your code to a GitHub repository
2. Ensure these files are in the root of your repository:
   - `main.py`: The Flask application entry point
   - `render_requirements.txt`: Dependencies for Render.com
   - `render.yaml`: Render Blueprint configuration file
   - `Procfile`: Process type declaration for Render

### 2. Deploy to Render.com

#### Option 1: One-Click Deploy with Blueprint

1. Sign up for [Render](https://render.com/) using your GitHub account
2. Click the "New" button and select "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file and set up your services
5. Review the configuration and click "Apply"

#### Option 2: Manual Setup

1. Sign up for [Render](https://render.com/) using your GitHub account
2. Create a new PostgreSQL database:
   - Click "New" > "PostgreSQL"
   - Choose a name like "shopee-postgres"
   - Select the Free plan
   - Click "Create Database"
3. Create a new Web Service:
   - Click "New" > "Web Service"
   - Connect your GitHub repository
   - Name the service "shopee-data-api"
   - Set the Runtime to "Python"
   - Set the Build Command to `pip install -r render_requirements.txt`
   - Set the Start Command to `gunicorn --bind 0.0.0.0:$PORT --workers=2 main:app`
   - Select the Free plan
   - Under Environment Variables, add:
     - `DATABASE_URL`: Copy from your PostgreSQL database info
     - `SESSION_SECRET`: Generate a secure random string
   - Click "Create Web Service"

### 3. Test Your Deployment

1. Once deployment is complete, Render will provide a URL for your service
2. Visit the URL to access your application
3. Test the API endpoints and frontend functionality

## Updating Your Application

1. Push changes to your GitHub repository
2. Render will automatically deploy updates

## Custom Domain (Optional)

For a more professional appearance, you can add a custom domain:

1. Purchase a domain from a provider like Namecheap or GoDaddy
2. In Render, go to your web service settings
3. Click "Custom Domain"
4. Follow the instructions to add and verify your domain

## Cost Considerations

- **Free Tier**: 750 hours per month (enough to run one service 24/7)
- **PostgreSQL Free Tier**: 1GB storage, automatic daily backups for 7 days
- **Limitations**:
  - Service will sleep after 15 minutes of inactivity
  - Cold starts take a few seconds
  - Limited computing resources

## Production Considerations

If your usage grows beyond the free tier:

1. Upgrade to a paid plan starting at $7/month for the web service
2. Upgrade to a paid database plan starting at $7/month for additional storage
3. The total cost for basic production hosting would be around $14/month

## Troubleshooting

- **Application Crashes**: Check the Render logs for error messages
- **Database Connection Issues**: Verify the DATABASE_URL environment variable
- **Slow Performance**: Consider upgrading to a paid plan for more resources
- **Cold Start Delays**: Normal for free tier, upgrade to eliminate these

## Additional Resources

- [Render Documentation](https://render.com/docs)
- [Render Blueprint Documentation](https://render.com/docs/blueprint-spec)
- [Render PostgreSQL Documentation](https://render.com/docs/databases)
