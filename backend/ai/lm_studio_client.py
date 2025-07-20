"""
LM Studio client for AI-powered content analysis and filtering.
"""
import openai
import requests
from typing import List, Dict, Any, Optional
import json
import logging

logger = logging.getLogger(__name__)

class LMStudioClient:
    def __init__(self, base_url: str = None, api_key: str = "lm-studio"):
        import os
        # Try environment variables first
        if base_url is None:
            lm_host = os.environ.get('LM_STUDIO_HOST')
            lm_port = os.environ.get('LM_STUDIO_PORT', '1234')
            
            if lm_host:
                self.base_url = f"http://{lm_host}:{lm_port}"
                logger.info(f"Using LM Studio from env: {lm_host}:{lm_port}")
            else:
                # Try Windows host IP for WSL, fallback to localhost
                import subprocess
                try:
                    # Get Windows host IP for WSL
                    result = subprocess.run(['ip', 'route', 'show'], capture_output=True, text=True)
                    host_ip = None
                    for line in result.stdout.split('\n'):
                        if 'default' in line:
                            host_ip = line.split()[2]
                            break
                    
                    if host_ip and host_ip != '127.0.0.1':
                        self.base_url = f"http://{host_ip}:1234"
                        logger.info(f"Using Windows host IP for LM Studio: {host_ip}")
                    else:
                        self.base_url = "http://localhost:1234"
                except:
                    self.base_url = "http://localhost:1234"
        else:
            self.base_url = base_url.rstrip('/v1')  # Remove /v1 if present
            
        self.api_key = api_key
        
        # Configure openai for older version
        openai.api_base = f"{self.base_url}/v1"
        openai.api_key = api_key
        
    def is_available(self) -> bool:
        """Check if LM Studio is running and accessible."""
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                models = models_data.get('data', []) if isinstance(models_data, dict) else []
                return len(models) > 0
            return False
        except Exception as e:
            logger.error(f"LM Studio not available: {e}")
            return False
    
    def _get_available_model(self) -> str:
        """Get the first available model."""
        try:
            response = requests.get(f"{self.base_url}/v1/models", timeout=5)
            if response.status_code == 200:
                models_data = response.json()
                models = models_data.get('data', []) if isinstance(models_data, dict) else []
                if models:
                    return models[0]['id']
            raise Exception("No models available")
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
            # Use the known model from LM Studio
            return "mistralai/mistral-7b-instruct-v0.3"
    
    def generate_embedding(self, text: str, model: str = "text-embedding-ada-002") -> Optional[List[float]]:
        """Generate embeddings for text content."""
        try:
            # LM Studio may not have embedding models, so we'll simulate with a hash-based approach
            # In production, you'd use a proper embedding model
            import hashlib
            import numpy as np
            
            # Create a simple hash-based embedding (for demo purposes)
            # Replace this with actual embedding model when available
            text_hash = hashlib.md5(text.encode()).hexdigest()
            # Convert hash to vector (384 dimensions like many embedding models)
            vector = []
            for i in range(0, len(text_hash), 2):
                vector.append(int(text_hash[i:i+2], 16) / 255.0)
            
            # Pad to standard embedding size
            while len(vector) < 384:
                vector.append(0.0)
            
            return vector[:384]
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None
    
    def categorize_article(self, title: str, content: str, model: str = None, category_prefs: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Categorize an article and extract metadata."""
        if model is None:
            model = self._get_available_model()
        
        # Build preference context if provided
        pref_context = ""
        if category_prefs:
            pref_context = "\n\nCategory Preferences:\n"
            for pref in category_prefs:
                pref_context += f"- {pref['category']}: Look for content about {', '.join(pref['keywords'])}\n"
        
        prompt = f"""Analyze this news article and provide a JSON response with the following structure:
{{
    "category": "one of: technology, politics, business, science, health, sports, entertainment, fashion, world",
    "sentiment": "positive, negative, or neutral",
    "importance": "high, medium, or low",
    "topics": ["list", "of", "key", "topics"],
    "summary": "brief one-sentence summary",
    "political_bias": -0.2,
    "bias_confidence": 0.8,
    "bias_reasoning": "Detailed explanation of why this bias score was assigned, including specific language choices, framing decisions, source selection, and perspective indicators that influenced the assessment.",
    "relevance_boost": 0.0
}}

For political bias analysis:
- -1.0 to -0.5: Left-leaning (progressive, liberal perspective)
- -0.5 to -0.2: Slight left lean
- -0.2 to 0.2: Neutral or non-political
- 0.2 to 0.5: Slight right lean  
- 0.5 to 1.0: Right-leaning (conservative perspective)

For bias_reasoning, analyze and explain:
1. Language choices (loaded words, emotional language, descriptive adjectives)
2. Framing decisions (how the story is presented, what's emphasized)
3. Source selection (which voices are included/excluded, credibility indicators)
4. Perspective indicators (whose viewpoint is prioritized, balance of coverage)
5. Context and implications (what's included/omitted from the broader context)

Note: 
- Fashion category includes: streetwear, high fashion, vintage clothing, designer brands, fashion trends, style guides, fashion weeks, and clothing culture.
- Set relevance_boost to 0.5 if the article matches any category preferences listed above.
{pref_context}

Title: {title}
Content: {content[:1000]}...

Respond only with valid JSON, no other text."""
        
        try:
            # Use direct requests instead of openai library
            # Note: Some models in LM Studio only support user/assistant roles
            combined_prompt = f"You are a news article analyzer. Respond only with valid JSON.\n\n{prompt}"
            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": combined_prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.1
            }
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                result_text = data['choices'][0]['message']['content'].strip()
                
                # Extract JSON from response (in case there's extra text)
                start = result_text.find('{')
                end = result_text.rfind('}') + 1
                if start != -1 and end != 0:
                    result_text = result_text[start:end]
                
                result = json.loads(result_text)
                return result
            else:
                raise Exception(f"HTTP {response.status_code}")
        except Exception as e:
            logger.error(f"Error categorizing article: {e}")
            return {
                "category": "uncategorized",
                "sentiment": "neutral", 
                "importance": "medium",
                "topics": [],
                "summary": title,
                "political_bias": 0.0,
                "bias_confidence": 0.0,
                "bias_reasoning": "Unable to analyze bias due to AI processing error.",
                "relevance_boost": 0.0
            }
    
    def calculate_relevance_score(self, article_embedding: List[float], 
                                 user_preferences: List[float], 
                                 model: str = None) -> float:
        """Calculate relevance score between article and user preferences."""
        try:
            # Simple cosine similarity
            import numpy as np
            
            if not article_embedding or not user_preferences:
                return 0.5  # Default relevance
                
            # Normalize vectors
            article_vec = np.array(article_embedding)
            user_vec = np.array(user_preferences)
            
            # Cosine similarity
            dot_product = np.dot(article_vec, user_vec)
            norms = np.linalg.norm(article_vec) * np.linalg.norm(user_vec)
            
            if norms == 0:
                return 0.5
                
            similarity = dot_product / norms
            
            # Convert to 0-1 range
            return (similarity + 1) / 2
            
        except Exception as e:
            logger.error(f"Error calculating relevance: {e}")
            return 0.5
    
    def summarize_article(self, content: str, model: str = None) -> str:
        """Generate a brief summary of an article."""
        if model is None:
            model = self._get_available_model()
        
        prompt = f"Summarize this news article in 1-2 sentences, focusing on the key facts:\n\n{content[:2000]}..."
        
        try:
            # Use direct requests instead of openai library
            # Note: Some models in LM Studio only support user/assistant roles
            combined_prompt = f"You are a news summarizer. Provide concise, factual summaries.\n\n{prompt}"
            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": combined_prompt}
                ],
                "max_tokens": 100,
                "temperature": 0.1
            }
            
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data['choices'][0]['message']['content'].strip()
            else:
                raise Exception(f"HTTP {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error summarizing article: {e}")
            return "Summary not available."