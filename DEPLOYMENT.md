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

### Step 3: Deploy Frontend

1. Click **"Create Static Site"**
2. Wait for deployment (3-5 minutes)
3. You'll get a URL like: `https://youlytics-frontend.onrender.com`

### Step 4: Update CORS Settings (Important!)

Now that you have the frontend URL, update the backend to allow requests from it.

**Option A: Using Render Dashboard**
1. Go to your backend service on Render
2. Add environment variable:
   ```
   FRONTEND_URL=https://youlytics-frontend.onrender.com
   ```
3. This would require modifying `app.py` to use this variable in CORS settings

**Option B: Quick Fix (for testing)**
The current CORS setup in `app.py` uses `CORS(app)` which allows all origins. This works for testing but is not recommended for production.

## ✅ Part 3: Test Your Deployment

### Test Backend API

1. **Health Check**: Open `https://youlytics-backend.onrender.com/`
   - Should see the welcome JSON

2. **Test Registration** (using curl or Postman):
   ```bash
   curl -X POST https://youlytics-backend.onrender.com/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"test123"}'
   ```
   - Should receive a JWT token

### Test Frontend Application

1. Open `https://youlytics-frontend.onrender.com/`
2. **Sign Up** with a new account
3. **Log In** with your credentials
4. **Test Analysis**:
   - Enter a YouTube URL (e.g., `https://www.youtube.com/watch?v=dQw4w9WgXcQ`)
   - Select "Comments Only" or "Full Analysis"
   - Click "Analyze"
   - Verify results display correctly

## 🔄 Making Updates

### Update Backend
1. Push changes to GitHub
2. Render will automatically detect and redeploy
3. Check deployment logs on Render dashboard

### Update Frontend
1. Update frontend code
2. If changing API URL, update `.env.production`
3. Push to GitHub
4. Render will rebuild and redeploy

## ⚠️ Important Notes

### Free Tier Limitations
- **Backend**: 
  - Spins down after 15 minutes of inactivity
  - First request after sleep may take 30-60 seconds
  - 750 hours/month free (enough for one service)
  
- **Frontend**: 
  - 100GB bandwidth/month
  - Static sites don't sleep

### Database Persistence
- **Current Setup**: Uses SQLite (`users.db`) which may not persist on Render's free tier
- **Recommendation**: Upgrade to PostgreSQL for production:
  1. Create a PostgreSQL database on Render (free tier available)
  2. Update `app.py` to use PostgreSQL instead of SQLite
  3. Add database connection string to environment variables

### API Rate Limits
- YouTube API has quota limits (10,000 units/day for free tier)
- Each comment analysis request uses ~1-5 units depending on comment count
- Monitor usage in Google Cloud Console

## 🐛 Troubleshooting

### Backend Returns 500 Error
- Check Render logs: Dashboard → Your Service → Logs
- Verify all environment variables are set correctly
- Ensure YouTube API key is valid

### Frontend Can't Connect to Backend
- Check browser console for CORS errors
- Verify `REACT_APP_API_BASE_URL` in `.env.production` is correct
- Ensure backend is running (check Render dashboard)

### Analysis Takes Too Long / Fails
- First request after backend sleep is slow
- Long videos with many comments may timeout
- Check backend logs for specific errors

### "Token is invalid" Error
- Clear browser localStorage and cookies
- Re-login to get a fresh token
- Check that JWT_SECRET is consistent across backend deployments

## 🎯 Next Steps (Optional Improvements)

1. **Custom Domain**: 
   - Add your own domain in Render settings
   - Update DNS records to point to Render

2. **Database Upgrade**:
   - Set up PostgreSQL on Render
   - Migrate SQLite data to PostgreSQL

3. **CORS Hardening**:
   - Update CORS settings to only allow your frontend domain
   - Add FRONTEND_URL environment variable

4. **Monitoring**:
   - Set up uptime monitoring (e.g., UptimeRobot)
   - Enable Render email notifications

5. **Performance**:
   - Upgrade to paid tier for no sleep time
   - Add caching for frequently analyzed videos
   - Implement request queuing for long-running analyses

## 📞 Need Help?

- **Render Docs**: https://render.com/docs
- **YouTube API Docs**: https://developers.google.com/youtube/v3
- Check the logs on Render dashboard for detailed error messages

---

**Congratulations! Your YouLytics application is now live! 🎉**
