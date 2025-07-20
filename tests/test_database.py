"""Test database functionality."""
import pytest
import sqlite3
from datetime import datetime

class TestDatabaseManager:
    """Test database operations."""
    
    def test_database_initialization(self, test_db):
        """Test that database initializes correctly."""
        # Check that tables exist
        cursor = test_db.connection.cursor()
        
        # Check articles table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='articles'")
        assert cursor.fetchone() is not None
        
        # Check feeds table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='feeds'")
        assert cursor.fetchone() is not None
        
        # Check user_interactions table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_interactions'")
        assert cursor.fetchone() is not None
        
        # Check category_preferences table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='category_preferences'")
        assert cursor.fetchone() is not None
    
    def test_insert_feed(self, test_db):
        """Test inserting a feed."""
        feed_info = {
            'title': 'Test Feed',
            'description': 'A test RSS feed',
            'url': 'https://example.com/feed.xml',
            'last_updated': datetime.now().isoformat()
        }
        
        feed_id = test_db.insert_feed(feed_info)
        assert feed_id is not None
        assert isinstance(feed_id, int)
        
        # Verify feed was inserted
        feeds = test_db.get_active_feeds()
        assert len(feeds) == 1
        assert feeds[0]['title'] == 'Test Feed'
    
    def test_insert_article(self, test_db):
        """Test inserting an article."""
        # First insert a feed
        feed_info = {
            'title': 'Test Feed',
            'description': 'A test RSS feed',
            'url': 'https://example.com/feed.xml',
            'last_updated': datetime.now().isoformat()
        }
        feed_id = test_db.insert_feed(feed_info)
        
        # Then insert an article
        article_data = {
            'title': 'Test Article',
            'content': 'This is a test article content.',
            'url': 'https://example.com/article1',
            'published_date': datetime.now().isoformat(),
            'feed_id': feed_id,
            'category': 'technology',
            'sentiment': 'neutral',
            'importance': 'medium',
            'topics': 'AI, testing',
            'political_bias': 0.1,
            'bias_confidence': 0.8,
            'bias_reasoning': 'Mostly neutral content'
        }
        
        article_id = test_db.insert_article(article_data)
        assert article_id is not None
        assert isinstance(article_id, int)
        
        # Verify article was inserted
        article = test_db.get_article_by_id(article_id)
        assert article is not None
        assert article['title'] == 'Test Article'
        assert article['category'] == 'technology'
    
    def test_get_articles_with_filters(self, test_db):
        """Test getting articles with various filters."""
        # Insert test data first
        feed_info = {
            'title': 'Test Feed',
            'description': 'A test RSS feed',
            'url': 'https://example.com/feed.xml',
            'last_updated': datetime.now().isoformat()
        }
        feed_id = test_db.insert_feed(feed_info)
        
        # Insert multiple articles
        for i in range(5):
            article_data = {
                'title': f'Test Article {i}',
                'content': f'This is test article {i} content.',
                'url': f'https://example.com/article{i}',
                'published_date': datetime.now().isoformat(),
                'feed_id': feed_id,
                'category': 'technology' if i % 2 == 0 else 'science',
                'sentiment': 'neutral',
                'importance': 'medium',
                'topics': 'testing',
                'political_bias': 0.0,
                'bias_confidence': 0.5,
                'bias_reasoning': 'Neutral content'
            }
            test_db.insert_article(article_data)
        
        # Test filter by category
        tech_articles = test_db.get_articles(category='technology')
        assert len(tech_articles) == 3  # 0, 2, 4
        
        science_articles = test_db.get_articles(category='science')
        assert len(science_articles) == 2  # 1, 3
        
        # Test limit
        limited_articles = test_db.get_articles(limit=3)
        assert len(limited_articles) == 3
        
        # Test offset
        offset_articles = test_db.get_articles(limit=3, offset=2)
        assert len(offset_articles) == 3
    
    def test_record_user_interaction(self, test_db):
        """Test recording user interactions."""
        # Insert test article first
        feed_info = {
            'title': 'Test Feed',
            'description': 'A test RSS feed',
            'url': 'https://example.com/feed.xml',
            'last_updated': datetime.now().isoformat()
        }
        feed_id = test_db.insert_feed(feed_info)
        
        article_data = {
            'title': 'Test Article',
            'content': 'Test content',
            'url': 'https://example.com/article',
            'published_date': datetime.now().isoformat(),
            'feed_id': feed_id,
            'category': 'technology',
            'sentiment': 'neutral',
            'importance': 'medium',
            'topics': 'testing',
            'political_bias': 0.0,
            'bias_confidence': 0.5,
            'bias_reasoning': 'Neutral'
        }
        article_id = test_db.insert_article(article_data)
        
        # Record interaction
        test_db.record_user_interaction(article_id, 'like', 1.0)
        
        # Verify interaction was recorded
        cursor = test_db.connection.cursor()
        cursor.execute(
            "SELECT * FROM user_interactions WHERE article_id = ? AND action = ?",
            (article_id, 'like')
        )
        interaction = cursor.fetchone()
        assert interaction is not None
    
    def test_category_preferences(self, test_db):
        """Test category preference operations."""
        # Test upsert (insert)
        success = test_db.upsert_category_preference(
            'technology', ['AI', 'machine learning'], 1.5
        )
        assert success is True
        
        # Test get preferences
        preferences = test_db.get_category_preferences()
        assert len(preferences) == 1
        assert preferences[0]['category'] == 'technology'
        assert 'AI' in preferences[0]['keywords']
        
        # Test upsert (update)
        success = test_db.upsert_category_preference(
            'technology', ['AI', 'robotics'], 2.0
        )
        assert success is True
        
        # Verify update
        preferences = test_db.get_category_preferences()
        assert len(preferences) == 1  # Still only one record
        assert 'robotics' in preferences[0]['keywords']
        assert preferences[0]['priority'] == 2.0
        
        # Test delete
        success = test_db.delete_category_preference('technology')
        assert success is True
        
        # Verify deletion
        preferences = test_db.get_category_preferences()
        assert len(preferences) == 0
    
    def test_update_article_ai_summary(self, test_db):
        """Test updating article AI summary."""
        # Insert test article
        feed_info = {
            'title': 'Test Feed',
            'description': 'A test RSS feed', 
            'url': 'https://example.com/feed.xml',
            'last_updated': datetime.now().isoformat()
        }
        feed_id = test_db.insert_feed(feed_info)
        
        article_data = {
            'title': 'Test Article',
            'content': 'Test content',
            'url': 'https://example.com/article',
            'published_date': datetime.now().isoformat(),
            'feed_id': feed_id,
            'category': 'technology',
            'sentiment': 'neutral',
            'importance': 'medium',
            'topics': 'testing',
            'political_bias': 0.0,
            'bias_confidence': 0.5,
            'bias_reasoning': 'Neutral'
        }
        article_id = test_db.insert_article(article_data)
        
        # Update AI summary
        test_summary = "This is a test AI summary."
        test_db.update_article_ai_summary(article_id, test_summary)
        
        # Verify update
        article = test_db.get_article_by_id(article_id)
        assert article['ai_summary'] == test_summary