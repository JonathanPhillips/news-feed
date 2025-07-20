"""Test AI functionality."""
import pytest
from unittest.mock import Mock, patch
import requests

class TestLMStudioClient:
    """Test LM Studio client functionality."""
    
    def test_is_available_success(self):
        """Test LM Studio availability check when service is up."""
        from ai.lm_studio_client import LMStudioClient
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            client = LMStudioClient()
            assert client.is_available() == True
    
    def test_is_available_failure(self):
        """Test LM Studio availability check when service is down."""
        from ai.lm_studio_client import LMStudioClient
        
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError()
            
            client = LMStudioClient()
            assert client.is_available() == False
    
    def test_categorize_article_success(self):
        """Test article categorization when LM Studio responds."""
        from ai.lm_studio_client import LMStudioClient
        
        mock_response_text = '''
        {
            "category": "technology",
            "sentiment": "positive",
            "importance": "high",
            "topics": ["AI", "machine learning"],
            "confidence": 0.95
        }
        '''
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_response_text
            mock_post.return_value = mock_response
            
            client = LMStudioClient()
            result = client.categorize_article("Test article content")
            
            assert result["category"] == "technology"
            assert result["sentiment"] == "positive"
            assert result["importance"] == "high"
            assert "AI" in result["topics"]
    
    def test_categorize_article_invalid_response(self):
        """Test article categorization with invalid JSON response."""
        from ai.lm_studio_client import LMStudioClient
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "Invalid JSON response"
            mock_post.return_value = mock_response
            
            client = LMStudioClient()
            result = client.categorize_article("Test article content")
            
            # Should return default values when JSON parsing fails
            assert result["category"] == "general"
            assert result["sentiment"] == "neutral"
            assert result["importance"] == "medium"
    
    def test_political_bias_in_categorization(self):
        """Test political bias analysis integrated in categorization."""
        from ai.lm_studio_client import LMStudioClient
        
        mock_response_text = '''
        {
            "category": "politics",
            "sentiment": "neutral",
            "importance": "high",
            "topics": ["election", "policy"],
            "confidence": 0.95,
            "political_bias": -0.3,
            "bias_confidence": 0.85,
            "bias_reasoning": "The article shows a slight liberal bias due to word choice and framing."
        }
        '''
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = mock_response_text
            mock_post.return_value = mock_response
            
            client = LMStudioClient()
            result = client.categorize_article("Test political article", "Content about policy changes.")
            
            assert result["political_bias"] == -0.3
            assert result["bias_confidence"] == 0.85
            assert "liberal bias" in result["bias_reasoning"]
    
    def test_summarize_article_success(self):
        """Test article summarization."""
        from ai.lm_studio_client import LMStudioClient
        
        expected_summary = "This is a test summary of the article content."
        
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = expected_summary
            mock_post.return_value = mock_response
            
            client = LMStudioClient()
            result = client.summarize_article("Long article content to summarize")
            
            assert result == expected_summary
    
    def test_network_error_handling(self):
        """Test handling of network errors."""
        from ai.lm_studio_client import LMStudioClient
        
        with patch('requests.post') as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError()
            
            client = LMStudioClient()
            
            # Should handle network errors gracefully
            result = client.categorize_article("Test title", "Test content")
            assert result["category"] == "general"
            assert result["political_bias"] == 0.0
            
            summary = client.summarize_article("Test content")
            assert summary == "Summary not available - AI service connection failed."