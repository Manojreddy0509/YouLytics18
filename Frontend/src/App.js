import React, { useState, useEffect } from 'react';
import { BarChart3, MessageSquare, ThumbsUp, ThumbsDown, Minus, Loader, FileText, Play, Users, Sparkles, AlertCircle, LogOut, User } from 'lucide-react';
import './App.css';
import Login from './Components/Login';
import Signup from './Components/Signup';

const App = () => {
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [analysisType, setAnalysisType] = useState('full');
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [showAuth, setShowAuth] = useState(true);
  const [isLogin, setIsLogin] = useState(true);

  // Check if user is already logged in
  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    
    if (savedToken && savedUser) {
      setToken(savedToken);
      setUser(JSON.parse(savedUser));
      setShowAuth(false);
    }
  }, []);

  const handleLogin = (userData, userToken) => {
    setUser(userData);
    setToken(userToken);
    setShowAuth(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setToken(null);
    setShowAuth(true);
    setData(null);
  };

  const analyzeContent = async () => {
    if (!user) {
      setError('Please login to use this feature');
      return;
    }

    if (!url) {
      setError('Please enter a YouTube URL');
      return;
    }

    setLoading(true);
    setError('');
    setData(null);
    
    try {
      let endpoint = '';
      switch(analysisType) {
        case 'comments':
          endpoint = '/analyze-comments';
          break;
        case 'summary':
          endpoint = '/summarize-video';
          break;
        case 'full':
          endpoint = '/full-analysis';
          break;
        default:
          endpoint = '/full-analysis';
      }

      const response = await fetch(`http://127.0.0.1:5001${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Server error: ${response.status}`);
      }
      
      const result = await response.json();
      setData(result);
    } catch (err) {
      setError(`Failed to connect to the server. Make sure the backend is running on http://localhost:5001. Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      analyzeContent();
    }
  };

  const StatCard = ({ title, count, percentage, color, icon }) => (
    <div className={`stat-card ${color}`}>
      <div className="stat-header">
        {icon}
        <h3>{title}</h3>
      </div>
      <div className="stat-content">
        <span className="stat-count">{count}</span>
        <span className="stat-percentage">{percentage}%</span>
      </div>
      <div className="stat-bar">
        <div 
          className={`stat-bar-fill ${color}`}
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
    </div>
  );

  const CommentSection = ({ comments, title, color }) => (
    <div className="comment-section">
      <h3 className={`section-title ${color}`}>
        <div className="title-content">
          {title === 'Positive Comments' && <ThumbsUp size={18} />}
          {title === 'Negative Comments' && <ThumbsDown size={18} />}
          {title === 'Neutral Comments' && <Minus size={18} />}
          {title}
        </div>
        <span className="comment-count">{comments.length}</span>
      </h3>
      <div className="comments-list">
        {comments.length > 0 ? (
          comments.map((item, index) => (
            <div key={index} className="comment-card">
              <div className="comment-header">
                <span className="comment-number">#{index + 1}</span>
                <div className={`sentiment-dot ${color}`}></div>
              </div>
              <p className="comment-text">{item.comment}</p>
            </div>
          ))
        ) : (
          <div className="no-comments">
            <Minus size={24} />
            <p>No {title.toLowerCase()} found</p>
          </div>
        )}
      </div>
    </div>
  );

  const SummarySection = ({ summaryData }) => {
    if (!summaryData || summaryData.error) {
      return (
        <div className="summary-section">
          <div className="section-header">
            <FileText className="section-icon" />
            <h2>Video Summary</h2>
            <span className="status-badge error">Unavailable</span>
          </div>
          <div className="error-state">
            <AlertCircle size={32} />
            <p>{summaryData?.error || 'Summary not available. Please install required dependencies.'}</p>
          </div>
        </div>
      );
    }

    return (
      <div className="summary-section">
        <div className="section-header">
          <FileText className="section-icon" />
          <h2>Video Summary</h2>
          <span className="status-badge success">
            {summaryData.section_count || summaryData.chunk_count || 0} sections
          </span>
        </div>
        
        <div className="summary-content">
          {/* Final Summary */}
          <div className="summary-card highlight">
            <div className="card-header">
              <Sparkles size={18} />
              <h3>Key Summary</h3>
            </div>
            <div className="final-summary">
              {summaryData.final_summary}
            </div>
          </div>

          {/* Transcription Preview */}
          {summaryData.transcription_preview && (
            <div className="summary-card">
              <div className="card-header">
                <FileText size={18} />
                <h3>Transcription Preview</h3>
                <span className="text-length">{summaryData.transcription_length} chars</span>
              </div>
              <div className="preview-text">
                {summaryData.transcription_preview}
                {summaryData.transcription_length > 500 && (
                  <span className="text-more">... (continued)</span>
                )}
              </div>
            </div>
          )}

          {/* Section Summaries */}
          {summaryData.section_summaries && summaryData.section_summaries.length > 0 && (
            <div className="summary-card">
              <div className="card-header">
                <BarChart3 size={18} />
                <h3>Detailed Breakdown</h3>
                <span className="section-count">{summaryData.section_summaries.length} points</span>
              </div>
              <div className="section-summaries">
                {summaryData.section_summaries.map((section, index) => (
                  <div key={index} className="section-item">
                    <div className="section-number">{index + 1}</div>
                    <div className="section-content">
                      {section.replace('Section ${index + 1}: ', '')}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Full Summary */}
          {summaryData.full_summary && (
            <div className="summary-card">
              <div className="card-header">
                <FileText size={18} />
                <h3>Complete Analysis</h3>
              </div>
              <div className="full-summary">
                {summaryData.full_summary.split('\n\n').map((paragraph, index) => (
                  <p key={index} className="summary-paragraph">
                    {paragraph}
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderHeader = () => (
    <header className="header">
      <div className="header-content">
        <div className="brand">
          <div className="logo">
            <Sparkles className="logo-icon" />
          </div>
          <div className="brand-text">
            <h1 className="brand-title">YouLytics</h1>
            <p className="brand-subtitle">Advanced YouTube Analysis Platform</p>
          </div>
        </div>
        
        {user && (
          <div className="user-info">
            <User size={16} />
            <span>{user.email}</span>
            <button onClick={handleLogout} className="logout-btn">
              <LogOut size={16} />
              Logout
            </button>
          </div>
        )}
      </div>
    </header>
  );

  // Show authentication if user is not logged in
  if (showAuth) {
    return (
      <div className="app">
        {renderHeader()}
        <main className="main">
          {isLogin ? (
            <Login onLogin={handleLogin} switchToSignup={() => setIsLogin(false)} />
          ) : (
            <Signup onLogin={handleLogin} switchToLogin={() => setIsLogin(true)} />
          )}
        </main>
      </div>
    );
  }

  return (
    <div className="app">
      {renderHeader()}

      {/* Main Content */}
      <main className="main">
        {/* Analysis Control */}
        <div className="control-section">
          <div className="analysis-type-selector">
            <div className="type-buttons">
              <button 
                className={`type-btn ${analysisType === 'full' ? 'active' : ''}`}
                onClick={() => setAnalysisType('full')}
              >
                <Play size={18} />
                Full Analysis
                <span>Comments + Summary</span>
              </button>
              <button 
                className={`type-btn ${analysisType === 'comments' ? 'active' : ''}`}
                onClick={() => setAnalysisType('comments')}
              >
                <Users size={18} />
                Comments Only
                <span>Sentiment Analysis</span>
              </button>
              <button 
                className={`type-btn ${analysisType === 'summary' ? 'active' : ''}`}
                onClick={() => setAnalysisType('summary')}
              >
                <FileText size={18} />
                Summary Only
                <span>Video Content</span>
              </button>
            </div>
          </div>

          <div className="input-section">
            <div className="input-container">
              <div className="input-wrapper">
                <input
                  type="text"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Paste YouTube URL here..."
                  className="url-input"
                  disabled={loading}
                />
                <div className="input-decoration"></div>
              </div>
              <button 
                onClick={analyzeContent} 
                disabled={loading}
                className={`analyze-btn ${analysisType}`}
              >
                {loading ? (
                  <>
                    <Loader className="spinner" size={20} />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Sparkles size={20} />
                    {analysisType === 'comments' ? 'Analyze Comments' : 
                     analysisType === 'summary' ? 'Summarize Video' : 
                     'Run Full Analysis'}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="error-message">
            <AlertCircle size={20} />
            {error}
          </div>
        )}

        {/* Info Message */}
        {!data && !error && !loading && (
          <div className="info-message">
            <div className="info-icon">🎯</div>
            <div className="info-content">
              <h3>Ready to Analyze</h3>
              <p>
                {analysisType === 'comments' && 'Enter a YouTube URL to analyze comment sentiment and engagement'}
                {analysisType === 'summary' && 'Enter a YouTube URL to transcribe and summarize video content'}
                {analysisType === 'full' && 'Enter a YouTube URL for complete analysis including comments and video summary'}
              </p>
            </div>
          </div>
        )}

        {/* Loading State */}
        {loading && (
          <div className="loading-section">
            <div className="loading-content">
              <Loader className="loading-spinner" size={48} />
              <div className="loading-text">
                <h3>
                  {analysisType === 'comments' && 'Analyzing Comments...'}
                  {analysisType === 'summary' && 'Processing Video...'}
                  {analysisType === 'full' && 'Running Complete Analysis...'}
                </h3>
                <p>This may take a few moments</p>
              </div>
            </div>
          </div>
        )}

        {/* Results */}
        {data && !loading && (
          <div className="results-section">
            {/* Comments Analysis */}
            {(data.comments_analysis || data.total_comments) && (
              <div className="analysis-section">
                <div className="section-header">
                  <Users className="section-icon" />
                  <h2>Comment Analysis</h2>
                  <span className="status-badge">
                    {data.comments_analysis?.total_comments || data.total_comments} comments
                  </span>
                </div>

                {/* Stats Grid */}
                <div className="stats-grid">
                  <div className="total-card">
                    <MessageSquare className="total-icon" />
                    <div className="total-content">
                      <span className="total-label">Total Comments Analyzed</span>
                      <span className="total-count">{data.comments_analysis?.total_comments || data.total_comments}</span>
                    </div>
                  </div>
                  
                  <StatCard
                    title="Positive"
                    count={data.comments_analysis?.positive?.count || data.positive?.count}
                    percentage={data.comments_analysis?.positive?.percentage || data.positive?.percentage}
                    color="positive"
                    icon={<ThumbsUp size={20} />}
                  />
                  
                  <StatCard
                    title="Negative"
                    count={data.comments_analysis?.negative?.count || data.negative?.count}
                    percentage={data.comments_analysis?.negative?.percentage || data.negative?.percentage}
                    color="negative"
                    icon={<ThumbsDown size={20} />}
                  />
                  
                  <StatCard
                    title="Neutral"
                    count={data.comments_analysis?.neutral?.count || data.neutral?.count}
                    percentage={data.comments_analysis?.neutral?.percentage || data.neutral?.percentage}
                    color="neutral"
                    icon={<Minus size={20} />}
                  />
                </div>

                {/* Comments Sections */}
                <div className="comments-sections">
                  <CommentSection
                    comments={data.comments_analysis?.positive?.comments || data.positive?.comments || []}
                    title="Positive Comments"
                    color="positive"
                  />
                  
                  <CommentSection
                    comments={data.comments_analysis?.negative?.comments || data.negative?.comments || []}
                    title="Negative Comments"
                    color="negative"
                  />
                  
                  <CommentSection
                    comments={data.comments_analysis?.neutral?.comments || data.neutral?.comments || []}
                    title="Neutral Comments"
                    color="neutral"
                  />
                </div>
              </div>
            )}

            {/* Video Summary */}
            {(data.video_summary || analysisType === 'summary') && (
              <SummarySection summaryData={data.video_summary || data} />
            )}

            {/* Reset Button */}
            <div className="action-section">
              <button 
                onClick={() => {
                  setData(null);
                  setUrl('');
                  setError('');
                }}
                className="reset-btn"
              >
                <Sparkles size={18} />
                Analyze Another Video
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="footer">
        <div className="footer-content">
          <p>YouLytics &copy; 2024 - Advanced YouTube Analytics Platform</p>
          <div className="footer-links">
            <span>Comment Analysis</span>
            <span>•</span>
            <span>Video Summarization</span>
            <span>•</span>
            <span>Sentiment Tracking</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;