# Deploying to Deta Space

This guide will walk you through deploying the Shopee Data API to Deta Space.

## Prerequisites

1. Create a [Deta Space](https://deta.space) account if you don't have one
2. Install the [Space CLI](https://deta.space/docs/en/build/reference/cli)

## Setup Steps

### 1. Install the Space CLI

For Windows (PowerShell):
```powershell
iwr https://get.deta.dev/space-cli.ps1 -useb | iex
```

For Mac/Linux:
```bash
curl -fsSL https://get.deta.dev/space-cli.sh | sh
```

### 2. Login to Space

```bash
space login
```

### 3. Initialize Your Project

Navigate to your project directory and run:

```bash
space new
```

This will create a `.space` directory in your project.

### 4. Configure Environment Variables

When you deploy your app, you'll need to set the following environment variables:

- `DATABASE_URL`: Your PostgreSQL database connection string
- `SESSION_SECRET`: A secure random string for session management

These are already configured in the Spacefile, and you'll be prompted to enter them during deployment.

### 5. Deploy Your App

```bash
space push
```

This will deploy your app to Deta Space. You'll see a URL where your app is accessible.

### 6. Release Your App (Optional)

If you want to make your app available to others, you can release it:

```bash
space release
```

To make it visible on Deta Space Discovery, add the `--listed` flag:

```bash
space release --listed
```

## Database Setup

For Deta Space deployment, you'll need to use an external PostgreSQL database. We recommend using [NeonDB](https://neon.tech) for a free PostgreSQL database that works well with Deta Space.

1. Create a database on NeonDB or your preferred PostgreSQL provider
2. Get the connection string in the format: `postgresql://username:password@host:port/database`
3. Use this connection string as your `DATABASE_URL` environment variable

## Troubleshooting

- If you encounter any issues with the deployment, check the logs in the Deta Space dashboard
- Make sure your database is accessible from Deta Space (public or properly configured for external access)
- Ensure all required environment variables are set correctly

## Additional Resources

- [Deta Space Documentation](https://deta.space/docs)
- [Spacefile Reference](https://deta.space/docs/en/build/reference/spacefile)
- [Discovery.md Reference](https://deta.space/docs/en/build/reference/discovery)
