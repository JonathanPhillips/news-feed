"""
Main application entry point for the news feed backend.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime

from ai.lm_studio_client import LMStudioClient
from content.feed_parser import FeedParser, DEFAULT_FEEDS
from database.models import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI News Feed", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
db = DatabaseManager()
lm_studio = LMStudioClient()
parser = FeedParser()

# Pydantic models for request validation
class InteractionRequest(BaseModel):
    action: str
    value: float = 1.0

class FeedRequest(BaseModel):
    url: str

class PreferenceRequest(BaseModel):
    category: str
    keywords: List[str]
    priority: float = 1.0

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Starting AI News Feed backend...")
    
    # Check if LM Studio is available
    if not lm_studio.is_available():
        logger.warning("LM Studio is not available. AI features will be limited.")
    
    # Add default feeds if database is empty
    feeds = db.get_active_feeds()
    if not feeds:
        logger.info("Adding default RSS feeds...")
        for feed_url in DEFAULT_FEEDS:
            feed_info = parser.get_feed_info(feed_url)
            db.insert_feed(feed_info)

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI News Feed API",
        "version": "1.0.0",
        "lm_studio_available": lm_studio.is_available()
    }

@app.get("/articles")
async def get_articles(
    limit: int = 20,
    offset: int = 0,
    category: Optional[str] = None,
    min_relevance: float = 0.0,
    read_status: Optional[bool] = None
) -> Dict[str, Any]:
    """Get filtered articles with pagination."""
    articles = db.get_articles(
        limit=limit,
        offset=offset,
        category=category,
        min_relevance=min_relevance,
        read_status=read_status
    )
    
    return {
        "articles": articles,
        "count": len(articles),
        "limit": limit,
        "offset": offset
    }

@app.get("/feeds")
async def get_feeds() -> List[Dict[str, Any]]:
    """Get all active RSS feeds."""
    return db.get_active_feeds()

@app.post("/feeds")
async def add_feed(request: FeedRequest) -> Dict[str, Any]:
    """Add a new RSS feed."""
    try:
        feed_info = parser.get_feed_info(request.url)
        feed_id = db.insert_feed(feed_info)
        
        if feed_id:
            return {"message": "Feed added successfully", "feed_id": feed_id}
        else:
            raise HTTPException(status_code=400, detail="Failed to add feed")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/refresh")
async def refresh_feeds() -> Dict[str, Any]:
    """Refresh all feeds and process articles with AI."""
    try:
        feeds = db.get_active_feeds()
        preferences = db.get_category_preferences()
        total_articles = 0
        
        for feed in feeds:
            logger.info(f"Refreshing feed: {feed['title']}")
            articles = parser.parse_feed(feed['url'])
            
            for article in articles:
                # Generate AI analysis if LM Studio is available
                if lm_studio.is_available():
                    # Generate embedding
                    text = f"{article['title']} {article['content']}"
                    embedding = lm_studio.generate_embedding(text)
                    article['embedding'] = embedding
                    
                    # Categorize article with preferences
                    ai_analysis = lm_studio.categorize_article(
                        article['title'], 
                        article['content'],
                        category_prefs=preferences
                    )
                    article.update(ai_analysis)
                    
                    # Apply relevance boost from AI analysis
                    base_relevance = article.get('relevance_score', 0.5)
                    boost = ai_analysis.get('relevance_boost', 0.0)
                    article['relevance_score'] = min(1.0, base_relevance + boost)
                
                # Insert into database
                article_id = db.insert_article(article)
                if article_id:
                    total_articles += 1
        
        return {
            "message": f"Refreshed {len(feeds)} feeds",
            "new_articles": total_articles
        }
        
    except Exception as e:
        logger.error(f"Error refreshing feeds: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/articles/{article_id}/interact")
async def record_interaction(
    article_id: int,
    request: InteractionRequest
) -> Dict[str, Any]:
    """Record user interaction with an article."""
    try:
        db.record_user_interaction(article_id, request.action, request.value)
        return {"message": "Interaction recorded"}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/articles/{article_id}/summary")
async def generate_ai_summary(article_id: int) -> Dict[str, Any]:
    """Generate an AI summary for a specific article."""
    try:
        # Get the article
        article = db.get_article_by_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        # Check if we already have an AI summary
        if article.get('ai_summary'):
            return {
                "summary": article['ai_summary'],
                "cached": True
            }
        
        # Generate new summary if LM Studio is available
        if lm_studio.is_available():
            full_content = f"{article['title']} - {article['content']}"
            ai_summary = lm_studio.summarize_article(full_content)
            
            # Save the summary to database
            db.update_article_ai_summary(article_id, ai_summary)
            
            return {
                "summary": ai_summary,
                "cached": False
            }
        else:
            raise HTTPException(status_code=503, detail="AI service not available")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate summary")

@app.get("/articles/{article_id}/bias-analysis")
async def get_bias_analysis(article_id: int) -> Dict[str, Any]:
    """Get detailed bias analysis for a specific article."""
    try:
        # Get the article
        article = db.get_article_by_id(article_id)
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        bias_info = {
            "article_id": article_id,
            "title": article['title'],
            "political_bias": article.get('political_bias', 0.0),
            "bias_confidence": article.get('bias_confidence', 0.0),
            "bias_reasoning": article.get('bias_reasoning', "No bias analysis available."),
            "category": article.get('category', 'uncategorized')
        }
        
        # Add bias interpretation
        bias_value = bias_info['political_bias']
        if bias_value <= -0.5:
            bias_info['bias_interpretation'] = "Left-leaning (progressive, liberal perspective)"
            bias_info['bias_label'] = "Left"
        elif bias_value <= -0.2:
            bias_info['bias_interpretation'] = "Slight left lean"
            bias_info['bias_label'] = "Left-lean"
        elif bias_value >= 0.5:
            bias_info['bias_interpretation'] = "Right-leaning (conservative perspective)"
            bias_info['bias_label'] = "Right"
        elif bias_value >= 0.2:
            bias_info['bias_interpretation'] = "Slight right lean"
            bias_info['bias_label'] = "Right-lean"
        else:
            bias_info['bias_interpretation'] = "Neutral or non-political"
            bias_info['bias_label'] = "Neutral"
        
        return bias_info
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting bias analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to get bias analysis")

@app.get("/preferences")
async def get_preferences() -> List[Dict[str, Any]]:
    """Get all category preferences."""
    return db.get_category_preferences()

@app.post("/preferences")
async def set_preference(request: PreferenceRequest) -> Dict[str, Any]:
    """Set or update a category preference."""
    try:
        if not request.category or not request.keywords:
            raise HTTPException(status_code=400, detail="Category and keywords required")
        
        success = db.upsert_category_preference(request.category, request.keywords, request.priority)
        if success:
            return {"message": "Preference saved successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to save preference")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.delete("/preferences/{category}")
async def delete_preference(category: str) -> Dict[str, Any]:
    """Delete a category preference."""
    success = db.delete_category_preference(category)
    if success:
        return {"message": "Preference deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Preference not found")

@app.post("/articles/{article_id}/read")
async def mark_article_read(article_id: int) -> Dict[str, Any]:
    """Mark an article as read."""
    try:
        success = db.mark_article_read(article_id)
        if success:
            return {"message": "Article marked as read"}
        else:
            raise HTTPException(status_code=404, detail="Article not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/articles/{article_id}/unread")
async def mark_article_unread(article_id: int) -> Dict[str, Any]:
    """Mark an article as unread."""
    try:
        success = db.mark_article_unread(article_id)
        if success:
            return {"message": "Article marked as unread"}
        else:
            raise HTTPException(status_code=404, detail="Article not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/stats/reading")
async def get_reading_stats() -> Dict[str, Any]:
    """Get reading statistics."""
    try:
        stats = db.get_read_count()
        return {
            "total_articles": stats["total"],
            "read_count": stats["read"],
            "unread_count": stats["unread"],
            "read_percentage": round((stats["read"] / stats["total"] * 100) if stats["total"] > 0 else 0, 1)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "lm_studio_available": lm_studio.is_available()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)