# YouLytics - Advanced YouTube Analytics Platform

![YouTube Analytics](https://img.shields.io/badge/YouTube-Analytics-red?logo=youtube)
![Flask](https://img.shields.io/badge/Flask-Backend-green?logo=flask)
![React](https://img.shields.io/badge/React-Frontend-blue?logo=react)

**YouLytics** is a powerful full-stack web application that provides comprehensive YouTube video analysis, including sentiment analysis of comments and AI-powered video summarization.

## ✨ Features

### 🎯 Comment Sentiment Analysis
- Analyze YouTube video comments using advanced NLP models
- Classify comments as Positive, Negative, or Neutral
- Visual statistics and percentage breakdowns
- Display categorized comments with sentiment indicators

### 📝 Video Summarization
- Automatic transcription of YouTube videos using Whisper
- AI-powered summarization of video content
- Section-by-section breakdown
- Key insights extraction

### 🔐 User Authentication
- Secure JWT-based authentication
- Email/password registration and login
- Protected API endpoints
- Persistent user sessions

### 🎨 Modern UI/UX
- Beautiful, responsive React interface
- Real-time analysis updates
- Interactive data visualization
- Dark mode design with glassmorphism effects

## 🏗️ Technology Stack

### Backend
- **Flask** - Python web framework
- **PyJWT** - JWT authentication
- **Transformers** - Sentiment analysis models
- **Whisper** - Video transcription
- **YouTube Data API v3** - Comment fetching
- **SQLite** - User database
- **Gunicorn** - Production server

### Frontend
- **React 18** - UI framework
- **Lucide React** - Icon library
- **CSS3** - Modern styling with animations

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 16+
- YouTube Data API key
- FFmpeg (for video transcription)

### Local Development

1. **Clone the repository**
   \`\`\`bash
   git clone https://github.com/yourusername/YouLytics18.git
   cd YouLytics18
   \`\`\`

2. **Set up the backend**
   \`\`\`bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\\Scripts\\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Configure environment variables
   cp .env.example .env
   # Edit .env and add your API keys
   
   # Run the backend
   python app.py
   \`\`\`

3. **Set up the frontend**
   \`\`\`bash
   cd Frontend
   npm install
   npm start
   \`\`\`



## 🌐 Deployment

See the **[DEPLOYMENT.md](DEPLOYMENT.md)** guide for detailed instructions on deploying to Render.com or other cloud platforms.

### Quick Deploy Summary

1. **Backend**: Deploy as Docker web service on Render
2. **Frontend**: Deploy as static site on Render
3. **Configure**: Set environment variables (API keys, secrets)
4. **Test**: Verify both services are communicating

## 📁 Project Structure

\`\`\`
YouLytics18/
├── app.py                 # Flask backend application
├── auth.py                # Authentication utilities
├── requirements.txt       # Python dependencies
├── Dockerfile            # Backend container config
├── Procfile              # Deployment config
├── Scraping/             # YouTube data fetching
│   ├── P1.py            # Video ID extraction
│   ├── P2.py            # Comment fetching
│   ├── model.py         # Sentiment analysis
│   └── transcribe.py    # Video transcription
├── Summarise/            # Video summarization
│   └── summarize.py     # AI summarization
└── Frontend/             # React application
    ├── src/
    │   ├── App.js       # Main application
    │   ├── App.css      # Styles
    │   └── Components/  # Auth components
    └── package.json     # Frontend dependencies
\`\`\`

## 🔑 Environment Variables

### Backend (.env)
\`\`\`bash
SECRET_KEY=your-flask-secret-key
JWT_SECRET=your-jwt-secret-key
YOUTUBE_API_KEY=your-youtube-api-key
\`\`\`

### Frontend (.env.production)
\`\`\`bash
REACT_APP_API_BASE_URL=https://your-backend-url.com
\`\`\`

## 📊 API Endpoints

- `POST /register` - Create new user account
- `POST /login` - Authenticate user
- `POST /analyze-comments` - Analyze video comments (protected)
- `POST /summarize-video` - Summarize video content (protected)
- `POST /full-analysis` - Complete analysis (protected)

## 🛠️ Development

### Running Tests
\`\`\`bash
# Backend tests
python -m pytest

# Frontend tests
cd Frontend && npm test
\`\`\`

