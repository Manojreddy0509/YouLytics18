import warnings
import logging

print("=" * 70)
print("📦 app.py module loading started...")
print("=" * 70)

# Suppress Python warnings
warnings.filterwarnings("ignore")
# Suppress Transformers library info/warnings
logging.getLogger("transformers").setLevel(logging.ERROR)

# Suppress Flask/Werkzeug info logs (only show errors)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv
from Scraping.comments import analyze_comments_logic
from Scraping.whisper_transcribe import transcribe_youtube
from Scraping.video_summarise import summarize_text

# Load environment variables
load_dotenv()

os.environ["TOKENIZERS_PARALLELISM"] = "false"
import uuid
import traceback
import sqlite3
import bcrypt
import jwt
import datetime
from jwt import ExpiredSignatureError, InvalidTokenError

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-secret-key')
JWT_SECRET = os.getenv('JWT_SECRET', 'fallback-jwt-secret')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY', '')

# Configure CORS - allow frontend domain
CORS(app, 
     origins=["https://youlytics-frontend.onrender.com", "http://localhost:3000"],
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "OPTIONS"]
)

print("=" * 60)
print("🚀 YouLytics Backend Starting...")
print(f"   Flask app initialized: {app.name}")
print(f"   CORS enabled: ✅")
print(f"   SECRET_KEY configured: {'✅' if os.getenv('SECRET_KEY') else '⚠️  Using fallback'}")
print(f"   JWT_SECRET configured: {'✅' if os.getenv('JWT_SECRET') else '⚠️  Using fallback'}")
print(f"   YOUTUBE_API_KEY configured: {'✅' if YOUTUBE_API_KEY else '❌ Missing'}")
print("=" * 60)

# Initialize database
def init_db():
    try:
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise

init_db()

# Authentication routes
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # Save to database
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        
        try:
            c.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, hashed_password))
            conn.commit()
            
            # Generate JWT token
            token = jwt.encode({
                'user_id': c.lastrowid,
                'email': email,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
            }, JWT_SECRET, algorithm='HS256')

            # PyJWT may return bytes depending on version; normalize to str for JSON.
            if isinstance(token, bytes):
                token = token.decode('utf-8')

            return jsonify({
                'message': 'User created successfully',
                'token': token,
                'user': {'email': email}
            }), 201

        except sqlite3.IntegrityError:
            return jsonify({'error': 'Email already exists'}), 400
        finally:
            conn.close()

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        # Get user from database
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT id, email, password FROM users WHERE email = ?', (email,))
        user = c.fetchone()
        conn.close()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
            # Generate JWT token
            token = jwt.encode({
                'user_id': user[0],
                'email': user[1],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
            }, JWT_SECRET, algorithm='HS256')

            # PyJWT may return bytes depending on version; normalize to str for JSON.
            if isinstance(token, bytes):
                token = token.decode('utf-8')

            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': {'email': user[1]}
            })
        else:
            return jsonify({'error': 'Invalid email or password'}), 401

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# JWT token required decorator
def token_required(f):
    def decorator(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({'error': 'Token is missing'}), 401

        # Expected: "Bearer <jwt>". Be tolerant of quotes / byte-string repr.
        token = auth_header.replace('Bearer ', '').strip().strip('"').strip("'")
        if token.startswith("b'") and token.endswith("'"):
            token = token[2:-1]

        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            request.user = data
        except ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except InvalidTokenError:
            return jsonify({'error': 'Token is invalid'}), 401

        return f(*args, **kwargs)

    decorator.__name__ = f.__name__
    return decorator

# Lazy loading for ML models to reduce startup memory
# Models will be loaded on first request, not at startup
COMMENT_AVAILABLE = True  # Set to True by default, will be checked on use
SUMMARIZE_AVAILABLE = True
analyzer = None  # Will be loaded lazily

def get_analyzer():
    """Lazy load the sentiment analyzer on first use"""
    global analyzer
    if analyzer is None:
        try:
            from Scraping.model import PretrainedSentimentAnalyzer
            analyzer = PretrainedSentimentAnalyzer()
            print("✅ Sentiment analyzer loaded")
        except Exception as e:
            print(f"❌ Failed to load analyzer: {e}")
            raise
    return analyzer

# Health check endpoint for deployment platforms
@app.route('/health')
def health():
    try:
        print("🏥 Health check requested")
        return jsonify({"status": "healthy", "timestamp": datetime.datetime.utcnow().isoformat()}), 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/')
def home():
    try:
        print("🏠 Home endpoint requested")
        return jsonify({
            "message": "YouLytics API is running!",
            "status": {
                "comment_analysis": COMMENT_AVAILABLE,
                "video_summarization": SUMMARIZE_AVAILABLE
            },
            "endpoints": {
                "/health": "GET - Health check",
                "/register": "POST - Create new account",
                "/login": "POST - Login to account",
                "/analyze-comments": "POST - Analyze comment sentiment",
                "/summarize-video": "POST - Summarize video content", 
                "/full-analysis": "POST - Complete analysis (comments + summary)"
            }
        })
    except Exception as e:
        print(f"❌ Home endpoint failed: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/analyze-comments', methods=['POST'])
@token_required
def analyze_comments():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        youtube_url = data.get('url')
        if not youtube_url:
            return jsonify({'error': 'YouTube URL is required'}), 400

        print(f"🔍 Analyzing comments for: {youtube_url}")

        # ✅ Call the single source of truth
        from Scraping.comments import analyze_comments_logic
        result = analyze_comments_logic(youtube_url, YOUTUBE_API_KEY)

        return jsonify({
            'type': 'comments',
            **result
        })

    except Exception as e:
        print(f"❌ Error in analyze-comments: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Comment analysis failed',
            'details': str(e)
        }), 500


@app.route('/summarize-video', methods=['POST'])
@token_required
def summarize_video():
    """
    Summarizes a YouTube video using:
    - yt-dlp + Whisper (audio → text)
    - DistilBART (text → summary)
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        youtube_url = data.get('url')
        if not youtube_url:
            return jsonify({'error': 'YouTube URL is required'}), 400

        print(f"🧠 Transcribing video with Whisper: {youtube_url}")

        # ✅ Audio-based transcription (NO captions)
        transcription = transcribe_youtube(youtube_url)

        print("📝 Summarizing transcription with DistilBART")

        # ✅ Abstractive summarization
        summary_data = summarize_text(transcription)

        return jsonify({
            'type': 'summary',
            'success': True,
            **summary_data
        }), 200

    except Exception as e:
        print(f"❌ Error in summarize-video: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Video summarization failed',
            'details': str(e)
        }), 500


from tasks import celery
from celery.result import AsyncResult

@app.route('/task-status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """
    Check status of a background task.
    """
    try:
        task_result = AsyncResult(task_id, app=celery)
        result = {
            "task_id": task_id,
            "status": task_result.status,
        }
        
        if task_result.status == 'SUCCESS':
            result["result"] = task_result.result
        elif task_result.status == 'FAILURE':
            result["error"] = str(task_result.result)
        
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/full-analysis', methods=['POST'])
@token_required
def full_analysis():
    """
    Performs complete analysis:
    - Comment sentiment analysis
    - Video transcription (Whisper)
    - Video summarization (DistilBART)
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        youtube_url = data.get('url')
        if not youtube_url:
            return jsonify({'error': 'YouTube URL is required'}), 400

        print(f"🎯 Starting full analysis for: {youtube_url}")

        # ✅ Comment analysis (single source of truth)
        from Scraping.comments import analyze_comments_logic
        comments_data = analyze_comments_logic(youtube_url, YOUTUBE_API_KEY)

        # ✅ Whisper transcription (audio-based)
        print("🧠 Transcribing video with Whisper...")
        transcription = transcribe_youtube(youtube_url)

        # ✅ DistilBART summarization
        print("📝 Summarizing transcription...")
        summary_data = summarize_text(transcription)

        return jsonify({
            'type': 'full',
            'success': True,
            'comments_analysis': comments_data,
            'video_summary': summary_data
        }), 200

    except Exception as e:
        print(f"❌ Error in full-analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Full analysis failed',
            'details': str(e)
        }), 500


if __name__ == '__main__':
    print("=" * 50)
    print("🚀 YouLytics API Starting...")
    print(f"   Comment Analysis: {'✅' if COMMENT_AVAILABLE else '❌'}")
    print(f"   Video Summarization: {'✅' if SUMMARIZE_AVAILABLE else '❌'}")
    print("   Authentication: ✅ Built-in")
    print("   Environment: ✅ Loaded")
    print("   Server: http://127.0.0.1:5000")
    print("=" * 50)
    print("Starting server...")
    app.run(debug=False, use_reloader=False, port=5000, host='127.0.0.1', threaded=True)
