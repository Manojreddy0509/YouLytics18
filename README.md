
# 🚀 YouLytics – Advanced YouTube Analytics Platform

**AI-Powered Sentiment Analysis, Comment Intelligence & Video Summarization**

> An end-to-end AI system that extracts YouTube comments, performs multilingual sentiment analysis using Transformer models, and generates concise audience-level summaries — all from a single YouTube link.

---

## 🌐 Live Demo (Deployed)

🚀 **Try the application here:**
👉 **[https://youlytics-frontend.onrender.com/](https://youlytics-frontend.onrender.com/)**

**How it works:**

* Paste any YouTube video link
* Analyze audience sentiment (Positive / Negative / Neutral)
* View sentiment distribution and AI-generated summary

> ⚠️ Note: The first request may take a few seconds due to cold start on free hosting.

---

## 🏗️ Deployment Architecture

YouLytics is deployed as a **decoupled full-stack system**:

* **Frontend:** React app deployed on **Render** (static site)
* **Backend:** Flask + ML inference deployed on **Hugging Face Spaces**
* **Communication:** Frontend consumes backend via REST APIs

This separation allows:

* Independent scaling
* Faster frontend load times
* Isolation of ML inference from UI logic

```
User Browser
     ↓
React Frontend (Render)
     ↓  REST API
Flask + ML Backend (Hugging Face Spaces)
     ↓
YouTube Data API + NLP Models
```

---

## 🔥 Why YouLytics Exists (Problem Statement)

YouTube creators, marketers, and analysts face real challenges:

* Thousands of unstructured comments
* Multilingual and code-mixed text (English, Hindi, Hinglish, etc.)
* No clear signal of audience sentiment
* Manual analysis is slow and impractical

**YouLytics converts raw YouTube comments into structured, actionable insights.**

---

## ✨ What This Project Does

Given a **YouTube link**, YouLytics:

1. Extracts **all comments and replies** using the YouTube Data API
2. Cleans and preprocesses noisy real-world text
3. Runs **ensemble sentiment analysis** using multiple Transformer models
4. Classifies comments into:

   * ✅ Positive
   * ❌ Negative
   * ⚪ Neutral
5. Generates a **concise summary** of audience opinions
6. Displays insights through a **modern web interface**

---

## 🧠 Core AI & ML Highlights

### ✔ Ensemble Sentiment Analysis

Instead of relying on a single model, YouLytics uses multiple pre-trained Transformers:

* **RoBERTa** – high accuracy on short social text
* **DistilBERT** – fast and efficient inference
* **Multilingual BERT** – supports non-English comments
* **XLM-RoBERTa** – strong performance on Indian languages and code-mixed text

➡ This improves robustness on real-world YouTube data.

---

### ✔ Language-Aware Processing

* Automatic language detection
* Handles English, Hindi, Hinglish, and multilingual comments
* Reduces bias toward English-only sentiment models

---

### ✔ Real-World Data Handling

* Handles pagination for large comment volumes
* Includes replies (not just top-level comments)
* API quota–friendly request throttling
* Graceful failure handling

---

## 🏗️ System Architecture (End-to-End Flow)

```
User (React UI)
     |
     |  YouTube Link
     ↓
Flask Backend (REST API)
     |
     |-- Extract Video ID
     |-- Fetch Comments (YouTube Data API)
     |-- Text Preprocessing & Language Detection
     |-- Sentiment Classification (Ensemble Models)
     |-- Comment Summarization
     ↓
Structured JSON Response
     ↓
React UI (Charts & Insights)
```

---

## 🧩 Tech Stack

### Frontend

* React
* JavaScript
* Axios
* Responsive UI

### Backend

* Flask
* Python
* REST APIs

### AI / ML

* Hugging Face Transformers
* RoBERTa, DistilBERT, BERT, XLM-RoBERTa
* LangDetect
* Ensemble inference

### External APIs

* YouTube Data API v3

---

## 📌 Key Features

✔ Accepts **any YouTube URL** (normal, short, Shorts)
✔ Extracts **top-level comments and replies**
✔ Handles **large comment volumes**
✔ Accurate **sentiment classification**
✔ **Audience opinion summarization**
✔ Clean frontend–backend separation
✔ Scalable and modular design

---

## 🛠️ Installation & Setup (Local)

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Manojreddy0509/YouLytics18.git
cd YouLytics18
```

### 2️⃣ Backend Setup

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
YOUTUBE_API_KEY=your_api_key_here
```

Run backend:

```bash
python app.py
```

---

### 3️⃣ Frontend Setup

```bash
cd frontend
npm install
npm start
```

---

## 🧪 Example Output

* 📊 Sentiment distribution (Positive / Negative / Neutral)
* 📈 Percentages and counts
* 🧾 AI-generated summary of audience opinions
* 🗂️ Labeled comments for further analysis

---

## 🎯 Real-World Use Cases

* Content creators analyzing audience feedback
* Marketing teams measuring campaign sentiment
* Brands monitoring product perception
* Researchers studying public opinion

---

## 🚧 Future Enhancements

* Emotion detection (joy, anger, sarcasm)
* Comment clustering and topic modeling
* Creator analytics dashboard
* Real-time live comment analysis
* CI/CD and cloud-scale deployment

---

## 👨‍💻 Author

**Manoj Reddy**
Final-year AI & Data Science Engineer
Focused on **applied NLP systems and full-stack ML products**

🔗 GitHub: [https://github.com/Manojreddy0509](https://github.com/Manojreddy0509)

---

## ⭐ Why This Project Stands Out

This is **not a tutorial project**.
It demonstrates:

* Real-world API integration
* Transformer-based NLP inference
* Full-stack system design
* Deployment across multiple platforms
* Product-oriented thinking

---

### ⭐ If you find this project useful, consider giving it a star.

---


