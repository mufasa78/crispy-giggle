# Shopee Data API - Streamlit Deployment Guide

## Overview

This guide explains how to deploy the Shopee Data API for free using Streamlit Cloud. Streamlit Cloud offers free hosting for Streamlit apps with continuous deployment from GitHub.

## Why Streamlit Cloud?

- **100% Free**: No credit card required
- **Custom Domain**: Option to use a custom domain
- **Private Apps**: Can make apps password-protected
- **GitHub Integration**: Automatic deployment from GitHub
- **Secrets Management**: Secure environment variables

## Deployment Steps

### 1. Prepare Your Repository

1. Push your code to a GitHub repository
2. Ensure these files are in the root of your repository:
   - `streamlit_app.py`: The Streamlit frontend app
   - `streamlit_requirements.txt`: Dependencies for Streamlit Cloud (rename to `requirements.txt` in the GitHub repo)

### 2. Set Up Streamlit Cloud

1. Sign up for [Streamlit Cloud](https://streamlit.io/cloud) using your GitHub account
2. Click "New app"
3. Select your repository, branch, and the `streamlit_app.py` file
4. Set the main module path to `streamlit_app.py`

### 3. Configure Environment Variables

1. In the Streamlit Cloud dashboard, go to your app's settings
2. Add the following secret:
   - `API_URL`: The URL of your Shopee Data API (e.g., `https://your-api-domain.com/api/v1`)

### 4. Deploying Your API Backend

For the backend API (Flask app), you have several options:

#### Option 1: Deploy to Render.com (Free Tier)

1. Sign up for [Render](https://render.com/)
2. Create a new Web Service
3. Connect your GitHub repository
4. Configure the build and start command:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT --workers=4 main:app`
5. Add the DATABASE_URL environment variable

#### Option 2: Deploy to Railway (Free Tier)

1. Sign up for [Railway](https://railway.app/)
2. Create a new project and connect your GitHub repository
3. Add a PostgreSQL database to your project
4. Configure environment variables:
   - `DATABASE_URL`: Automatically set by Railway
   - `SESSION_SECRET`: Your secure session secret
5. Deploy your service

### 5. Update the Streamlit App Configuration

After deploying your API backend, update the `API_URL` in Streamlit Cloud to point to your new API endpoint.

## Testing Your Deployment

1. Visit your Streamlit app URL
2. Enter an API key
3. Try extracting data from a Shopee URL
4. Verify that the data is correctly retrieved and displayed

## Cost Considerations

- **Streamlit Cloud**: Free tier includes 1 app with unlimited viewers
- **Render/Railway**: Free tiers include sleeping after periods of inactivity
  - Render: 750 hours per month free
  - Railway: $5 worth of resources free per month

## Scaling Considerations

If your usage grows beyond the free tier limits:

1. **Render**: Upgrade to a paid plan starting at $7/month
2. **Railway**: Continues charging based on usage after free credits
3. **Streamlit Cloud**: Upgrade to Team plan for more apps/features

## Limitations of Free Tier

- Services may sleep after periods of inactivity (30 minutes on Render)
- Cold starts might cause initial slowness
- Limited computing resources
- Database size restrictions

These limitations shouldn't impact light to moderate usage scenarios.
