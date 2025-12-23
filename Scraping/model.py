# model.py
# pip install transformers torch pandas numpy
import pandas as pd
import numpy as np
from collections import Counter
from transformers import pipeline
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PretrainedSentimentAnalyzer:
    def __init__(self):
        self.models = {}
        self.max_length = 512  # Maximum token length for most transformer models
        self.initialize_models()
    
    def initialize_models(self):
        """Initialize pre-trained models"""
        print("Loading pre-trained models...")
        try:
            # RoBERTa - Twitter specific model
            self.models['roberta'] = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                tokenizer="cardiffnlp/twitter-roberta-base-sentiment-latest",
                return_all_scores=True,
                truncation=True,
                max_length=self.max_length
            )
            # DistilBERT - General purpose
            self.models['distilbert'] = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                return_all_scores=True,
                truncation=True,
                max_length=self.max_length
            )
            # BERT - Multilingual sentiment
            self.models['bert'] = pipeline(
                "sentiment-analysis",
                model="nlptown/bert-base-multilingual-uncased-sentiment",
                return_all_scores=True,
                truncation=True,
                max_length=self.max_length
            )
            print("✓ All models loaded successfully")
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            raise
    
    def preprocess_text(self, text):
        """Preprocess text to handle long inputs and clean data"""
        if not text or not isinstance(text, str):
            return ""
        
        # Clean the text
        text = text.strip()
        
        # Truncate to reasonable character length (approx 4 chars per token)
        max_chars = self.max_length * 4
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
            
        return text
    
    def analyze_with_roberta(self, text):
        """Analyze sentiment using RoBERTa model"""
        try:
            processed_text = self.preprocess_text(text)
            result = self.models['roberta'](processed_text)
            sentiment_map = {'LABEL_0': 'negative', 'LABEL_1': 'neutral', 'LABEL_2': 'positive'}
            scores = {item['label']: item['score'] for item in result[0]}
            best_label = max(scores, key=scores.get)
            sentiment = sentiment_map.get(best_label, best_label.lower())
            return {'model': 'RoBERTa', 'sentiment': sentiment, 'confidence': scores[best_label]}
        except Exception as e:
            logger.warning(f"RoBERTa analysis failed: {e}")
            return {'model': 'RoBERTa', 'sentiment': 'neutral', 'confidence': 0.5}
    
    def analyze_with_distilbert(self, text):
        """Analyze sentiment using DistilBERT model"""
        try:
            processed_text = self.preprocess_text(text)
            result = self.models['distilbert'](processed_text)
            sentiment_map = {'NEGATIVE': 'negative', 'POSITIVE': 'positive'}
            scores = {item['label']: item['score'] for item in result[0]}
            best_label = max(scores, key=scores.get)
            sentiment = sentiment_map.get(best_label, best_label.lower())
            
            # Add neutral if confidence is low
            if scores[best_label] < 0.6:
                sentiment = 'neutral'
            return {'model': 'DistilBERT', 'sentiment': sentiment, 'confidence': scores[best_label]}
        except Exception as e:
            logger.warning(f"DistilBERT analysis failed: {e}")
            return {'model': 'DistilBERT', 'sentiment': 'neutral', 'confidence': 0.5}
    
    def analyze_with_bert(self, text):
        """Analyze sentiment using BERT model"""
        try:
            processed_text = self.preprocess_text(text)
            result = self.models['bert'](processed_text)
            scores = {item['label']: item['score'] for item in result[0]}
            best_label = max(scores, key=scores.get)
            
            # Convert star ratings to sentiment
            if '1' in best_label or '2' in best_label:
                sentiment = 'negative'
            elif '4' in best_label or '5' in best_label:
                sentiment = 'positive'
            else:
                sentiment = 'neutral'
            return {'model': 'BERT', 'sentiment': sentiment, 'confidence': scores[best_label]}
        except Exception as e:
            logger.warning(f"BERT analysis failed: {e}")
            return {'model': 'BERT', 'sentiment': 'neutral', 'confidence': 0.5}
    
    def ensemble_predict(self, text):
        """Combine predictions from all models using weighted voting"""
        if not text or not text.strip():
            return {
                'sentiment': 'neutral',
                'confidence': 0.5,
                'individual_predictions': [],
                'ensemble_method': 'fallback',
                'vote_counts': {'neutral': 3},
                'weighted_scores': {'neutral': 1.5}
            }
        
        predictions = []
        models_to_try = [
            self.analyze_with_roberta,
            self.analyze_with_distilbert, 
            self.analyze_with_bert
        ]
        
        for model_func in models_to_try:
            try:
                prediction = model_func(text)
                predictions.append(prediction)
            except Exception as e:
                logger.warning(f"Model {model_func.__name__} failed: {e}")
                # Add neutral prediction as fallback
                predictions.append({
                    'model': model_func.__name__.replace('analyze_with_', '').upper(),
                    'sentiment': 'neutral', 
                    'confidence': 0.5
                })
        
        # If all models failed, return neutral
        if not predictions:
            return {
                'sentiment': 'neutral',
                'confidence': 0.5,
                'individual_predictions': [],
                'ensemble_method': 'fallback',
                'vote_counts': {'neutral': 3},
                'weighted_scores': {'neutral': 1.5}
            }
        
        # Ensemble voting
        sentiment_votes = Counter([pred['sentiment'] for pred in predictions])
        weighted_votes = {}
        
        for pred in predictions:
            sentiment = pred['sentiment']
            confidence = pred['confidence']
            weighted_votes[sentiment] = weighted_votes.get(sentiment, 0) + confidence
        
        final_sentiment = max(weighted_votes, key=weighted_votes.get)
        final_confidence = weighted_votes[final_sentiment] / len(predictions)
        
        return {
            'sentiment': final_sentiment,
            'confidence': final_confidence,
            'individual_predictions': predictions,
            'ensemble_method': 'weighted_voting',
            'vote_counts': dict(sentiment_votes),
            'weighted_scores': weighted_votes
        }
    
    def analyze_single_comment(self, comment):
        """Analyze a single comment with error handling"""
        try:
            return self.ensemble_predict(comment)
        except Exception as e:
            logger.error(f"Error analyzing comment: {e}")
            return {
                'sentiment': 'neutral',
                'confidence': 0.5,
                'individual_predictions': [],
                'ensemble_method': 'error_fallback'
            }
    
    def analyze_all_comments(self, comments):
        """Analyze all comments with comprehensive error handling"""
        results = {'positive': [], 'negative': [], 'neutral': []}
        
        if not comments:
            return results
        
        print(f"Analyzing {len(comments)} comments...")
        
        for i, comment in enumerate(comments):
            if i % 10 == 0:
                print(f"Processed {i}/{len(comments)} comments...")
                
            if comment and isinstance(comment, str) and comment.strip():
                try:
                    result = self.analyze_single_comment(comment)
                    
                    # Add to results without individual predictions to reduce response size
                    results[result['sentiment']].append({
                        'comment': comment,
                        'confidence': round(result['confidence'], 3)
                    })
                    
                except Exception as e:
                    logger.error(f"Failed to process comment {i}: {e}")
                    # Add as neutral on error
                    results['neutral'].append({
                        'comment': comment,
                        'confidence': 0.5,
                        'error': str(e)
                    })
            else:
                # Skip empty comments
                continue
        
        print(f"Analysis complete: {len(results['positive'])} positive, {len(results['negative'])} negative, {len(results['neutral'])} neutral")
        return results

# Simple fallback analyzer for testing
class SimpleSentimentAnalyzer:
    """Simple rule-based sentiment analyzer as fallback"""
    def __init__(self):
        self.positive_words = {
            'good', 'great', 'excellent', 'amazing', 'awesome', 'fantastic', 'perfect',
            'love', 'wonderful', 'brilliant', 'outstanding', 'superb', 'terrific',
            'nice', 'cool', 'best', 'beautiful', 'happy', 'pleased', 'satisfied',
            'impressive', 'recommend', 'thanks', 'thank you', 'helpful', 'useful'
        }
        self.negative_words = {
            'bad', 'terrible', 'awful', 'horrible', 'worst', 'hate', 'disappointed',
            'disappointing', 'poor', 'waste', 'rubbish', 'garbage', 'trash',
            'boring', 'stupid', 'dumb', 'useless', 'pointless', 'awful',
            'annoying', 'frustrating', 'angry', 'mad', 'sucks', 'sucked'
        }
    
    def analyze_all_comments(self, comments):
        results = {'positive': [], 'negative': [], 'neutral': []}
        
        for comment in comments:
            if not comment or not isinstance(comment, str):
                results['neutral'].append({'comment': comment or ''})
                continue
                
            comment_lower = comment.lower()
            positive_count = sum(1 for word in self.positive_words if word in comment_lower)
            negative_count = sum(1 for word in self.negative_words if word in comment_lower)
            
            if positive_count > negative_count:
                results['positive'].append({'comment': comment})
            elif negative_count > positive_count:
                results['negative'].append({'comment': comment})
            else:
                results['neutral'].append({'comment': comment})
        
        return results

# Usage in Flask:
# from model import PretrainedSentimentAnalyzer, SimpleSentimentAnalyzer
# analyzer = PretrainedSentimentAnalyzer()  # Main analyzer
# fallback_analyzer = SimpleSentimentAnalyzer()  # Fallback
# sentiment_data = analyzer.analyze_all_comments(comments)