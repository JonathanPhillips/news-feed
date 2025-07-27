#!/usr/bin/env python3
"""Test refresh with a single fashion feed."""

import sys
sys.path.append('/home/jon/projects/news_feed')
sys.path.append('/home/jon/projects/news_feed/backend')

from backend.database.models import DatabaseManager
from backend.ai.lm_studio_client import LMStudioClient
from backend.content.feed_parser import FeedParser

def test_fashion_feed():
    """Test processing a single fashion feed."""
    
    db = DatabaseManager()
    lm_studio = LMStudioClient()
    parser = FeedParser()
    
    print("🔧 TESTING SINGLE FASHION FEED")
    print("=" * 50)
    
    if not lm_studio.is_available():
        print("❌ LM Studio not available!")
        return
    
    # Test Vogue feed
    vogue_url = "https://www.vogue.com/feed/rss"
    print(f"📡 Fetching from: {vogue_url}")
    
    # Parse feed
    articles = parser.parse_feed(vogue_url)
    print(f"📰 Parsed {len(articles)} articles")
    
    if not articles:
        print("❌ No articles found!")
        return
    
    # Process first 3 articles with AI
    preferences = db.get_category_preferences()
    processed = 0
    
    for i, article in enumerate(articles[:3]):
        print(f"\n🤖 Processing article {i+1}: {article['title'][:50]}...")
        
        try:
            # Generate AI analysis
            text = f"{article['title']} {article['content']}"
            embedding = lm_studio.generate_embedding(text)
            article['embedding'] = embedding
            
            ai_analysis = lm_studio.categorize_article(
                article['title'],
                article['content'],
                category_prefs=preferences
            )
            
            article.update(ai_analysis)
            
            print(f"   Category: {ai_analysis['category']}")
            print(f"   Topics: {ai_analysis['topics'][:3]}...")
            
            # Insert into database
            article_id = db.insert_article(article)
            if article_id:
                processed += 1
                print(f"   ✅ Saved as article {article_id}")
            else:
                print(f"   ❌ Failed to save")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n🎉 Successfully processed {processed}/3 articles!")

if __name__ == "__main__":
    test_fashion_feed()