"""
Unit tests for NLP Engine Service.

Tests cover:
- Text preprocessing
- Language detection
- Keyword extraction
- Severity term detection
"""

import pytest
from services.nlp_engine import NLPEngine, get_nlp_engine


class TestNLPEngine:
    """Test suite for NLP Engine functionality."""
    
    @pytest.fixture
    def nlp_engine(self):
        """Create NLP Engine instance for testing."""
        return NLPEngine()
    
    # Tests for text preprocessing (Requirement 3.1)
    
    def test_preprocess_text_removes_special_characters(self, nlp_engine):
        """Test that special characters are removed from text."""
        text = "Hello @#$% World! This is a test & complaint."
        result = nlp_engine.preprocess_text(text)
        assert "@" not in result
        assert "#" not in result
        assert "$" not in result
        assert "%" not in result
        assert "&" not in result
    
    def test_preprocess_text_normalizes_whitespace(self, nlp_engine):
        """Test that multiple spaces are normalized to single space."""
        text = "This    has     multiple    spaces"
        result = nlp_engine.preprocess_text(text)
        assert "  " not in result
        assert result == "this has multiple spaces"
    
    def test_preprocess_text_converts_to_lowercase(self, nlp_engine):
        """Test that text is converted to lowercase."""
        text = "URGENT: Water LEAKAGE in Main Street"
        result = nlp_engine.preprocess_text(text)
        assert result.islower()
        assert "urgent" in result
        assert "water" in result
    
    def test_preprocess_text_strips_whitespace(self, nlp_engine):
        """Test that leading and trailing whitespace is removed."""
        text = "   complaint text   "
        result = nlp_engine.preprocess_text(text)
        assert not result.startswith(" ")
        assert not result.endswith(" ")
    
    def test_preprocess_text_empty_input(self, nlp_engine):
        """Test preprocessing with empty input."""
        assert nlp_engine.preprocess_text("") == ""
        assert nlp_engine.preprocess_text(None) == ""
    
    # Tests for language detection (Requirement 3.2)
    
    def test_detect_language_english(self, nlp_engine):
        """Test language detection for English text."""
        text = "There is a water leakage in my street"
        result = nlp_engine.detect_language(text)
        assert result == 'en'
    
    def test_detect_language_short_text(self, nlp_engine):
        """Test language detection with very short text defaults to English."""
        text = "Hi"
        result = nlp_engine.detect_language(text)
        assert result == 'en'
    
    def test_detect_language_empty_text(self, nlp_engine):
        """Test language detection with empty text defaults to English."""
        result = nlp_engine.detect_language("")
        assert result == 'en'
    
    # Tests for translation (Requirement 3.2)
    
    def test_translate_to_english_already_english(self, nlp_engine):
        """Test that English text is not translated."""
        text = "This is already in English"
        result = nlp_engine.translate_to_english(text, 'en')
        assert result == text
    
    def test_translate_to_english_other_language(self, nlp_engine):
        """Test translation placeholder for non-English text."""
        text = "Hola mundo"
        result = nlp_engine.translate_to_english(text, 'es')
        # Currently returns original text as translation is not implemented
        assert result == text
    
    # Tests for keyword extraction (Requirements 3.1, 3.3)
    
    def test_extract_keywords_basic(self, nlp_engine):
        """Test keyword extraction from complaint text."""
        text = "water leakage problem in main street causing flooding"
        result = nlp_engine.extract_keywords(text)
        assert isinstance(result, list)
        assert len(result) > 0
        # Should extract meaningful words
        assert any(word in result for word in ['water', 'leakage', 'flooding', 'street'])
    
    def test_extract_keywords_removes_stopwords(self, nlp_engine):
        """Test that common stopwords are filtered out."""
        text = "there is a water leakage in the main street"
        result = nlp_engine.extract_keywords(text)
        # Stopwords like 'is', 'a', 'the', 'in' should not be in keywords
        assert 'is' not in result
        assert 'a' not in result
        assert 'the' not in result
    
    def test_extract_keywords_empty_text(self, nlp_engine):
        """Test keyword extraction with empty text."""
        result = nlp_engine.extract_keywords("")
        assert result == []
    
    def test_extract_keywords_top_n(self, nlp_engine):
        """Test that keyword extraction respects top_n parameter."""
        text = "water water water leakage leakage street flooding problem issue complaint"
        result = nlp_engine.extract_keywords(text, top_n=3)
        assert len(result) <= 3
    
    # Tests for severity term detection (Requirements 3.3, 3.4)
    
    def test_detect_severity_terms_fire(self, nlp_engine):
        """Test detection of 'fire' severity term."""
        text = "there is a fire in the building"
        result = nlp_engine.detect_severity_terms(text)
        assert 'fire' in result
    
    def test_detect_severity_terms_electric_shock(self, nlp_engine):
        """Test detection of 'electric shock' severity term."""
        text = "someone got electric shock from the pole"
        result = nlp_engine.detect_severity_terms(text)
        assert 'electric shock' in result
    
    def test_detect_severity_terms_multiple(self, nlp_engine):
        """Test detection of multiple severity terms."""
        text = "fire caused by electric shock leading to injury"
        result = nlp_engine.detect_severity_terms(text)
        assert 'fire' in result
        assert 'electric shock' in result
        assert 'injury' in result
        assert len(result) == 3
    
    def test_detect_severity_terms_all_terms(self, nlp_engine):
        """Test that all severity terms are detected."""
        severity_terms = [
            "fire", "electric shock", "accident", "flooding",
            "leakage", "collapse", "injury", "death"
        ]
        for term in severity_terms:
            text = f"there is a {term} situation"
            result = nlp_engine.detect_severity_terms(text)
            assert term in result, f"Failed to detect severity term: {term}"
    
    def test_detect_severity_terms_case_insensitive(self, nlp_engine):
        """Test that severity detection is case-insensitive."""
        text = "FIRE in the BUILDING causing INJURY"
        result = nlp_engine.detect_severity_terms(text)
        assert 'fire' in result
        assert 'injury' in result
    
    def test_detect_severity_terms_none_found(self, nlp_engine):
        """Test when no severity terms are present."""
        text = "routine maintenance request for street light"
        result = nlp_engine.detect_severity_terms(text)
        assert result == []
    
    def test_detect_severity_terms_empty_text(self, nlp_engine):
        """Test severity detection with empty text."""
        result = nlp_engine.detect_severity_terms("")
        assert result == []
    
    # Integration test for complete processing pipeline
    
    def test_process_complaint_complete_pipeline(self, nlp_engine):
        """Test the complete NLP processing pipeline."""
        raw_text = "URGENT!!! There is a FIRE and water LEAKAGE in Main Street #123"
        result = nlp_engine.process_complaint(raw_text)
        
        # Check all expected keys are present
        assert 'cleaned_text' in result
        assert 'language' in result
        assert 'translated_text' in result
        assert 'keywords' in result
        assert 'severity_terms' in result
        
        # Check cleaned text is processed
        assert result['cleaned_text'].islower()
        assert '!' not in result['cleaned_text']
        assert '#' not in result['cleaned_text']
        
        # Check language detection
        assert result['language'] == 'en'
        
        # Check keywords extracted
        assert len(result['keywords']) > 0
        
        # Check severity terms detected
        assert 'fire' in result['severity_terms']
        assert 'leakage' in result['severity_terms']
    
    def test_process_complaint_no_severity(self, nlp_engine):
        """Test processing complaint without severity terms."""
        raw_text = "Request for street light repair on Oak Avenue"
        result = nlp_engine.process_complaint(raw_text)
        
        assert result['severity_terms'] == []
        assert len(result['keywords']) > 0
        assert result['language'] == 'en'
    
    # Test singleton pattern
    
    def test_get_nlp_engine_singleton(self):
        """Test that get_nlp_engine returns the same instance."""
        engine1 = get_nlp_engine()
        engine2 = get_nlp_engine()
        assert engine1 is engine2
