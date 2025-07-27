"""
Database models and operations for the news feed application.
"""
import sqlite3
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = None):
        import os
        if db_path is None:
            db_path = os.environ.get('DATABASE_PATH', 'news_feed.db')
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Articles table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    content TEXT,
                    author TEXT,
                    published TIMESTAMP,
                    source_url TEXT,
                    guid TEXT UNIQUE,
                    category TEXT,
                    sentiment TEXT,
                    importance TEXT,
                    topics TEXT,  -- JSON array
                    summary TEXT,
                    ai_summary TEXT,  -- On-demand AI summary
                    political_bias REAL,  -- -1.0 (left) to 1.0 (right), 0 = neutral
                    bias_confidence REAL DEFAULT 0.0,  -- 0.0 to 1.0 confidence in bias assessment
                    bias_reasoning TEXT,  -- Detailed explanation of bias assessment
                    embedding BLOB,  -- Serialized embedding vector
                    relevance_score REAL DEFAULT 0.5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # RSS feeds table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS feeds (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    url TEXT UNIQUE NOT NULL,
                    description TEXT,
                    link TEXT,
                    language TEXT DEFAULT 'en',
                    active BOOLEAN DEFAULT 1,
                    last_fetched TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # User preferences and reading history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_interactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER,
                    action TEXT,  -- 'view', 'like', 'dislike', 'share', 'read_time'
                    value REAL,   -- Time spent reading, rating, etc.
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles (id)
                )
            ''')
            
            # User preference vector (learned from interactions)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY,
                    preference_vector BLOB,  -- Serialized preference embedding
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Category-specific preferences
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS category_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    keywords TEXT NOT NULL,  -- JSON array of keywords/topics
                    priority REAL DEFAULT 1.0,  -- How important this preference is
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(category)
                )
            ''')
            
            # Add read status column if it doesn't exist (migration)
            try:
                cursor.execute('ALTER TABLE articles ADD COLUMN read_status BOOLEAN DEFAULT 0')
                logger.info("Added read_status column to articles table")
            except sqlite3.OperationalError:
                # Column already exists
                pass
                
            # Add category column to feeds table if it doesn't exist (migration)
            try:
                cursor.execute('ALTER TABLE feeds ADD COLUMN category TEXT DEFAULT NULL')
                logger.info("Added category column to feeds table")
            except sqlite3.OperationalError:
                # Column already exists
                pass
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def insert_article(self, article_data: Dict[str, Any]) -> Optional[int]:
        """Insert or update an article in the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Convert topics list to JSON string
                topics_json = json.dumps(article_data.get('topics', []))
                
                cursor.execute('''
                    INSERT OR REPLACE INTO articles 
                    (title, url, content, author, published, source_url, guid, 
                     category, sentiment, importance, topics, summary, ai_summary,
                     political_bias, bias_confidence, bias_reasoning, embedding, relevance_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    article_data.get('title'),
                    article_data.get('url'),
                    article_data.get('content'),
                    article_data.get('author'),
                    article_data.get('published'),
                    article_data.get('source_url'),
                    article_data.get('guid'),
                    article_data.get('category'),
                    article_data.get('sentiment'),
                    article_data.get('importance'),
                    topics_json,
                    article_data.get('summary'),
                    article_data.get('ai_summary'),
                    article_data.get('political_bias'),
                    article_data.get('bias_confidence', 0.0),
                    article_data.get('bias_reasoning'),
                    self._serialize_embedding(article_data.get('embedding')),
                    article_data.get('relevance_score', 0.5)
                ))
                
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Error inserting article: {e}")
            return None
    
    def get_articles(self, limit: int = 50, offset: int = 0, 
                    category: Optional[str] = None,
                    min_relevance: float = 0.0,
                    read_status: Optional[bool] = None) -> List[Dict[str, Any]]:
        """Get articles from database with filtering and pagination."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = '''
                    SELECT * FROM articles 
                    WHERE relevance_score >= ?
                '''
                params = [min_relevance]
                
                if category:
                    query += ' AND category = ?'
                    params.append(category)
                
                if read_status is not None:
                    query += ' AND read_status = ?'
                    params.append(1 if read_status else 0)
                
                query += ' ORDER BY relevance_score DESC, published DESC LIMIT ? OFFSET ?'
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                articles = []
                for row in rows:
                    article = dict(row)
                    article['topics'] = json.loads(article.get('topics') or '[]')
                    article['embedding'] = self._deserialize_embedding(article.get('embedding'))
                    articles.append(article)
                
                return articles
                
        except Exception as e:
            logger.error(f"Error getting articles: {e}")
            return []
    
    def record_user_interaction(self, article_id: int, action: str, value: float = 1.0):
        """Record user interaction with an article."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO user_interactions (article_id, action, value)
                    VALUES (?, ?, ?)
                ''', (article_id, action, value))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error recording interaction: {e}")
    
    def update_article_ai_summary(self, article_id: int, ai_summary: str):
        """Update an article with AI-generated summary."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE articles SET ai_summary = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (ai_summary, article_id))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error updating AI summary: {e}")
    
    def get_article_by_id(self, article_id: int) -> Optional[Dict[str, Any]]:
        """Get a single article by ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM articles WHERE id = ?', (article_id,))
                row = cursor.fetchone()
                
                if row:
                    article = dict(row)
                    article['topics'] = json.loads(article.get('topics') or '[]')
                    article['embedding'] = self._deserialize_embedding(article.get('embedding'))
                    return article
                return None
                
        except Exception as e:
            logger.error(f"Error getting article: {e}")
            return None
    
    def insert_feed(self, feed_data: Dict[str, Any]) -> Optional[int]:
        """Insert a new RSS feed."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO feeds 
                    (title, url, description, link, language, active, category)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    feed_data.get('title'),
                    feed_data.get('url'),
                    feed_data.get('description'),
                    feed_data.get('link'),
                    feed_data.get('language', 'en'),
                    True,
                    feed_data.get('category')
                ))
                return cursor.lastrowid
                
        except Exception as e:
            logger.error(f"Error inserting feed: {e}")
            return None
    
    def get_active_feeds(self) -> List[Dict[str, Any]]:
        """Get all active RSS feeds."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM feeds WHERE active = 1')
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error getting feeds: {e}")
            return []
    
    def delete_feed(self, feed_id: int) -> bool:
        """Delete an RSS feed."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM feeds WHERE id = ?', (feed_id,))
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error deleting feed: {e}")
            return False
    
    def _serialize_embedding(self, embedding: Optional[List[float]]) -> Optional[bytes]:
        """Serialize embedding vector to bytes."""
        if embedding is None:
            return None
        try:
            import pickle
            return pickle.dumps(embedding)
        except Exception:
            return None
    
    def _deserialize_embedding(self, embedding_bytes: Optional[bytes]) -> Optional[List[float]]:
        """Deserialize embedding vector from bytes."""
        if embedding_bytes is None:
            return None
        try:
            import pickle
            return pickle.loads(embedding_bytes)
        except Exception:
            return None
    
    def get_category_preferences(self) -> List[Dict[str, Any]]:
        """Get all category preferences."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM category_preferences WHERE active = 1')
                prefs = []
                for row in cursor.fetchall():
                    pref = dict(row)
                    pref['keywords'] = json.loads(pref['keywords'])
                    prefs.append(pref)
                return prefs
        except Exception as e:
            logger.error(f"Error getting category preferences: {e}")
            return []
    
    def upsert_category_preference(self, category: str, keywords: List[str], priority: float = 1.0) -> bool:
        """Insert or update category preference."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO category_preferences 
                    (category, keywords, priority, active)
                    VALUES (?, ?, ?, 1)
                ''', (category, json.dumps(keywords), priority))
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving category preference: {e}")
            return False
    
    def delete_category_preference(self, category: str) -> bool:
        """Delete a category preference."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM category_preferences WHERE category = ?', (category,))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting category preference: {e}")
            return False

    def mark_article_read(self, article_id: int) -> bool:
        """Mark an article as read."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update read status
                cursor.execute(
                    'UPDATE articles SET read_status = 1 WHERE id = ?',
                    (article_id,)
                )
                update_count = cursor.rowcount
                
                # Record the view interaction if update was successful
                if update_count > 0:
                    cursor.execute(
                        'INSERT INTO user_interactions (article_id, action, value) VALUES (?, ?, ?)',
                        (article_id, 'read', 1.0)
                    )
                
                conn.commit()
                return update_count > 0
                
        except Exception as e:
            logger.error(f"Error marking article as read: {e}")
            return False

    def mark_article_unread(self, article_id: int) -> bool:
        """Mark an article as unread."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update read status
                cursor.execute(
                    'UPDATE articles SET read_status = 0 WHERE id = ?',
                    (article_id,)
                )
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error marking article as unread: {e}")
            return False

    def get_read_count(self) -> Dict[str, int]:
        """Get count of read vs unread articles."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT 
                        SUM(CASE WHEN read_status = 1 THEN 1 ELSE 0 END) as read_count,
                        SUM(CASE WHEN read_status = 0 THEN 1 ELSE 0 END) as unread_count,
                        COUNT(*) as total_count
                    FROM articles
                ''')
                
                row = cursor.fetchone()
                return {
                    "read": row[0] or 0,
                    "unread": row[1] or 0,
                    "total": row[2] or 0
                }
                
        except Exception as e:
            logger.error(f"Error getting read count: {e}")
            return {"read": 0, "unread": 0, "total": 0}