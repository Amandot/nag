"""
NLP Engine Service for processing complaint text.

This module provides Natural Language Processing capabilities including:
- Text preprocessing and cleaning
- Language detection and translation
- Keyword extraction
- Severity term detection
"""

import re
import logging
from typing import List, Tuple
from langdetect import detect, LangDetectException
from sklearn.feature_extraction.text import TfidfVectorizer
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

# Download required NLTK data (run once)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

logger = logging.getLogger(__name__)


class NLPEngine:
    """
    Natural Language Processing engine for complaint text analysis.
    """
    
    # Severity terms that indicate high-priority issues
    SEVERITY_TERMS = [
        "fire",
        "electric shock",
        "accident",
        "flooding",
        "leakage",
        "collapse",
        "injury",
        "death"
    ]
    
    def __init__(self):
        """Initialize the NLP Engine with required resources."""
        self.stop_words = set(stopwords.words('english'))
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=20,
            stop_words='english',
            ngram_range=(1, 2)
        )
        logger.info("NLP Engine initialized")
    
    def preprocess_text(self, text: str) -> str:
        """
        Clean and preprocess complaint text.
        
        Removes special characters, normalizes whitespace, and converts to lowercase.
        
        Args:
            text: Raw complaint text
            
        Returns:
            Cleaned and normalized text
            
        Requirements: 3.1
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep spaces and basic punctuation
        text = re.sub(r'[^a-z0-9\s.,-]', '', text)
        
        # Normalize whitespace (replace multiple spaces with single space)
        text = re.sub(r'\s+', ' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        logger.debug(f"Preprocessed text: {text[:100]}...")
        return text
    
    def detect_language(self, text: str) -> str:
        """
        Detect the language of the complaint text.
        
        Args:
            text: Complaint text
            
        Returns:
            ISO 639-1 language code (e.g., 'en', 'hi', 'es')
            Returns 'en' if detection fails
            
        Requirements: 3.2
        """
        if not text or len(text.strip()) < 3:
            logger.warning("Text too short for language detection, defaulting to 'en'")
            return 'en'
        
        try:
            lang = detect(text)
            logger.info(f"Detected language: {lang}")
            return lang
        except LangDetectException as e:
            logger.warning(f"Language detection failed: {e}, defaulting to 'en'")
            return 'en'
    
    def translate_to_english(self, text: str, source_lang: str) -> str:
        """
        Translate text to English if it's in another language.
        
        Note: This is a placeholder implementation. In production, integrate
        with Google Translate API or similar service.
        
        Args:
            text: Text to translate
            source_lang: Source language code
            
        Returns:
            Translated text (or original if already English)
            
        Requirements: 3.2
        """
        if source_lang == 'en':
            logger.debug("Text already in English, no translation needed")
            return text
        
        # TODO: Integrate with Google Translate API
        # For now, return original text with a warning
        logger.warning(
            f"Translation from {source_lang} to English not yet implemented. "
            "Returning original text."
        )
        return text
    
    def extract_keywords(self, text: str, top_n: int = 10) -> List[str]:
        """
        Extract important keywords from complaint text using TF-IDF.
        
        Args:
            text: Preprocessed complaint text
            top_n: Number of top keywords to extract
            
        Returns:
            List of extracted keywords
            
        Requirements: 3.1, 3.3
        """
        if not text:
            return []
        
        try:
            # Tokenize and remove stopwords
            tokens = word_tokenize(text)
            filtered_tokens = [
                word for word in tokens 
                if word.isalnum() and word not in self.stop_words and len(word) > 2
            ]
            
            if not filtered_tokens:
                return []
            
            # For single document, use simple frequency-based approach
            # In production with multiple documents, use TF-IDF vectorizer
            from collections import Counter
            word_freq = Counter(filtered_tokens)
            keywords = [word for word, _ in word_freq.most_common(top_n)]
            
            logger.debug(f"Extracted keywords: {keywords}")
            return keywords
            
        except Exception as e:
            logger.error(f"Keyword extraction failed: {e}")
            return []
    
    def detect_severity_terms(self, text: str) -> List[str]:
        """
        Detect severity terms in complaint text that indicate high-priority issues.
        
        Args:
            text: Preprocessed complaint text (should be lowercase)
            
        Returns:
            List of detected severity terms
            
        Requirements: 3.3, 3.4
        """
        if not text:
            return []
        
        detected_terms = []
        text_lower = text.lower()
        
        for term in self.SEVERITY_TERMS:
            if term in text_lower:
                detected_terms.append(term)
        
        if detected_terms:
            logger.info(f"Detected severity terms: {detected_terms}")
        
        return detected_terms
    
    def process_complaint(self, raw_text: str) -> dict:
        """
        Complete NLP processing pipeline for a complaint.
        
        Args:
            raw_text: Raw complaint text
            
        Returns:
            Dictionary containing:
                - cleaned_text: Preprocessed text
                - language: Detected language code
                - translated_text: English translation (if needed)
                - keywords: Extracted keywords
                - severity_terms: Detected severity terms
        """
        # Step 1: Detect language
        language = self.detect_language(raw_text)
        
        # Step 2: Translate if needed
        translated_text = self.translate_to_english(raw_text, language)
        
        # Step 3: Preprocess
        cleaned_text = self.preprocess_text(translated_text)
        
        # Step 4: Extract keywords
        keywords = self.extract_keywords(cleaned_text)
        
        # Step 5: Detect severity terms
        severity_terms = self.detect_severity_terms(cleaned_text)
        
        result = {
            'cleaned_text': cleaned_text,
            'language': language,
            'translated_text': translated_text if language != 'en' else raw_text,
            'keywords': keywords,
            'severity_terms': severity_terms
        }
        
        logger.info(f"NLP processing complete. Found {len(keywords)} keywords and {len(severity_terms)} severity terms")
        return result


# Singleton instance
_nlp_engine = None


def get_nlp_engine() -> NLPEngine:
    """
    Get or create the singleton NLP Engine instance.
    
    Returns:
        NLPEngine instance
    """
    global _nlp_engine
    if _nlp_engine is None:
        _nlp_engine = NLPEngine()
    return _nlp_engine
