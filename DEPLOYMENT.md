# 🚀 YouLytics Deployment Guide

This guide will walk you through deploying YouLytics (Flask backend + React frontend) to **Render.com** using their free tier.

## 📋 Prerequisites

1. **GitHub Account** - Your code should be pushed to a GitHub repository
2. **Render Account** - Sign up at [render.com](https://render.com)
3. **API Keys** - You'll need:
   - YouTube Data API key ([Get one here](https://console.cloud.google.com/apis/credentials))
   - Generate secrets for `SECRET_KEY` and `JWT_SECRET` (or use random strings)

## 🔧 Part 1: Deploy Backend (Flask API)

### Step 1: Prepare Your Repository

1. Ensure your latest code is pushed to GitHub
2. The backend files should be in the root directory:
   - `app.py`
   - `requirements.txt`
   - `Dockerfile`

### Step 2: Create Backend Web Service on Render

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `youlytics-backend` (or your preferred name)
   - **Region**: Choose closest to your users
   - **Branch**: `main` (or your default branch)
   - **Root Directory**: Leave blank (backend is in root)
   - **Runtime**: `Docker`
   - **Instance Type**: `Free`

### Step 3: Configure Environment Variables

In the **Environment** section, add these variables:

```
SECRET_KEY=<generate-a-random-secret-key>
JWT_SECRET=<generate-another-random-secret-key>
YOUTUBE_API_KEY=<your-youtube-api-key>
TOKENIZERS_PARALLELISM=false
```

**How to generate secret keys:**
```bash
# Run this in your terminal to generate random keys
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 4: Deploy Backend

1. Click **"Create Web Service"**
2. Wait for deployment (5-10 minutes for first deployment)
3. Once deployed, you'll get a URL like: `https://youlytics-backend.onrender.com`
4. **Copy this URL** - you'll need it for the frontend!

### Step 5: Verify Backend

Visit your backend URL in a browser. You should see:
```json
{
  "message": "YouLytics API is running!",
  "status": {
    "comment_analysis": true,
    "video_summarization": true
  }
}
```

## 🎨 Part 2: Deploy Frontend (React App)

### Step 1: Update Frontend Configuration

1. Create a `.env.production` file in the `Frontend/` directory:
   ```bash
   cd Frontend
   cp .env.production.example .env.production
   ```

2. Edit `.env.production` and update with your backend URL:
   ```
   REACT_APP_API_BASE_URL=https://youlytics-backend.onrender.com
   ```
   *(Replace with your actual backend URL from Part 1)*

3. Commit and push this change:
   ```bash
   git add Frontend/.env.production
   git commit -m "Add production environment configuration"
   git push
   ```

### Step 2: Create Frontend Static Site on Render

1. Go back to [Render Dashboard](https://dashboard.render.com/)
2. Click **"New +"** → **"Static Site"**
3. Select the same GitHub repository
4. Configure the service:
   - **Name**: `youlytics-frontend` (or your preferred name)
   - **Branch**: `main`
   - **Root Directory**: `Frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `build`





