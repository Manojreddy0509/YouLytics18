# 🚀 YouLytics – Advanced YouTube Analytics Platform

**AI-Powered Sentiment Analysis, Comment Intelligence & Video Summarization**

> A full-stack AI system that extracts YouTube comments, understands audience sentiment using multiple Transformer models, and generates meaningful summaries — all from a single YouTube link.

---

## 🔥 Why YouLytics Exists (Problem Statement)

YouTube creators, marketers, and analysts face a real problem:

* Thousands of comments
* Mixed languages (English, Hindi, Hinglish, regional languages)
* No clear signal of audience sentiment
* Manual analysis is impossible

**YouLytics solves this by converting raw YouTube comments into structured insights.**

---

## ✨ What This Project Does 

Given a **YouTube link**, YouLytics:

1. Extracts **all comments + replies** using YouTube Data API
2. Cleans and preprocesses text intelligently
3. Runs **ensemble sentiment analysis** using multiple pre-trained Transformer models
4. Classifies comments into:

   * ✅ Positive
   * ❌ Negative
   * ⚪ Neutral
5. Generates a **concise summary** of audience opinions
6. Displays results through a **modern web interface**

---

## 🧠 Core AI & ML Highlights 

### ✔ Ensemble Sentiment Analysis (Not Single Model)

Instead of relying on one model, YouLytics uses **multiple Transformers**:

* **RoBERTa** – high accuracy on short social text
* **DistilBERT** – fast inference
* **Multilingual BERT** – non-English comments
* **XLM-RoBERTa** – Indian languages + code-mixed text

➡ Improves robustness and real-world accuracy.

---

### ✔ Language-Aware Processing

* Automatically detects comment language
* Handles English, Hindi, Hinglish, and multilingual comments
* Prevents bias toward only English content

---

### ✔ Real-World Data Handling

* Handles pagination (thousands of comments)
* Includes replies (not just top-level comments)
* API-quota friendly request throttling
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
     |  Extract Video ID
     |  Fetch Comments (YouTube Data API)
     |  Preprocess + Language Detection
     |  Sentiment Classification (Ensemble Models)
     |  Comment Summarization
     ↓
Structured JSON Response
     ↓
React UI (Charts + Insights)
```

---

## 🧩 Tech Stack (Modern & Industry-Relevant)

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

* HuggingFace Transformers
* RoBERTa, DistilBERT, BERT, XLM-RoBERTa
* LangDetect
* Ensemble inference

### External APIs

* YouTube Data API v3

---


## 🌐 Live Demo

🚀 **Try the application here:**  
👉 https://youlytics-frontend.onrender.com/

Paste any YouTube video link to:
- Analyze audience sentiment (Positive / Negative / Neutral)
- View sentiment distribution
- Read an AI-generated summary of comments

> ⚠️ Note: Initial load may take a few seconds due to cold start on free hosting.


## 📌 Key Features

✔ Accepts **any YouTube URL** (normal, short, Shorts)
✔ Extracts **top-level comments + replies**
✔ Handles **large comment volumes**
✔ Accurate **sentiment classification**
✔ **Audience opinion summarization**
✔ Clean separation of frontend & backend
✔ Scalable & modular design

---

## 🛠️ Installation & Setup

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

Run Flask server:

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

* 📊 Sentiment Distribution (Positive / Negative / Neutral)
* 📈 Percentages & counts
* 🧾 Clean summary of audience opinions
* 🗂️ Labeled comments for deeper analysis

---

## 🎯 Real-World Use Cases

* Content creators analyzing audience feedback
* Marketing teams measuring campaign sentiment
* Brands monitoring product reviews
* Researchers studying public opinion

---

## 🚧 Future Enhancements

* Emotion detection (joy, anger, sarcasm)
* Comment clustering & topic modeling
* Creator dashboard with history tracking
* Real-time live comment analysis
* Deployment on cloud with CI/CD

---

## 👨‍💻 Author

**Manoj Reddy**
Final-year AI & Data Science Engineer
Focused on **applied AI, NLP systems, and full-stack ML products**

🔗 GitHub: [https://github.com/Manojreddy0509](https://github.com/Manojreddy0509)

---

## ⭐ Why This Project Stands Out

This is **not a tutorial project**.
This is a **real-world ML system** that demonstrates:

* API integration
* NLP engineering
* Model orchestration
* Full-stack deployment
* Product-level thinking

---

### ⭐ If you like this project, consider giving it a star — it helps more than you think.

---




