"""
RSS feed parser and content aggregation.
"""
import feedparser
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class FeedParser:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AI News Feed Reader 1.0'
        })
    
    def parse_feed(self, url: str) -> List[Dict[str, Any]]:
        """Parse RSS feed and return list of articles."""
        try:
            response = self.session.get(url, timeout=10)
            feed = feedparser.parse(response.content)
            
            articles = []
            for entry in feed.entries:
                article = self._extract_article_data(entry)
                if article:
                    articles.append(article)
            
            logger.info(f"Parsed {len(articles)} articles from {url}")
            return articles
            
        except Exception as e:
            logger.error(f"Error parsing feed {url}: {e}")
            return []
    
    def _extract_article_data(self, entry) -> Optional[Dict[str, Any]]:
        """Extract relevant data from feed entry."""
        try:
            # Get publication date
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime(*entry.published_parsed[:6])
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                pub_date = datetime(*entry.updated_parsed[:6])
            else:
                pub_date = datetime.now()
            
            # Get content
            content = ""
            if hasattr(entry, 'content') and entry.content:
                content = entry.content[0].value
            elif hasattr(entry, 'summary'):
                content = entry.summary
            elif hasattr(entry, 'description'):
                content = entry.description
            
            # Clean HTML from content
            content = self._clean_html(content)
            
            return {
                'title': entry.title if hasattr(entry, 'title') else 'No Title',
                'url': entry.link if hasattr(entry, 'link') else '',
                'content': content,
                'author': entry.author if hasattr(entry, 'author') else 'Unknown',
                'published': pub_date.isoformat(),
                'source_url': entry.link if hasattr(entry, 'link') else '',
                'guid': entry.id if hasattr(entry, 'id') else entry.link
            }
            
        except Exception as e:
            logger.error(f"Error extracting article data: {e}")
            return None
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text."""
        import re
        # Simple HTML tag removal
        clean_text = re.sub(r'<[^>]+>', '', text)
        # Remove extra whitespace
        clean_text = ' '.join(clean_text.split())
        return clean_text
    
    def get_feed_info(self, url: str) -> Dict[str, Any]:
        """Get information about the RSS feed."""
        try:
            response = self.session.get(url, timeout=10)
            feed = feedparser.parse(response.content)
            
            return {
                'title': feed.feed.title if hasattr(feed.feed, 'title') else 'Unknown Feed',
                'description': feed.feed.description if hasattr(feed.feed, 'description') else '',
                'url': url,
                'link': feed.feed.link if hasattr(feed.feed, 'link') else '',
                'language': feed.feed.language if hasattr(feed.feed, 'language') else 'en',
                'entry_count': len(feed.entries)
            }
            
        except Exception as e:
            logger.error(f"Error getting feed info for {url}: {e}")
            return {
                'title': 'Error',
                'description': f'Failed to parse feed: {e}',
                'url': url,
                'link': '',
                'language': 'en',
                'entry_count': 0
            }

# Default RSS feeds to get started
DEFAULT_FEEDS = [
    'https://feeds.bbci.co.uk/news/rss.xml',
    'https://rss.cnn.com/rss/edition.rss',
    'https://feeds.reuters.com/reuters/topNews',
    'https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml',
    'https://feeds.arstechnica.com/arstechnica/index',
    'https://feeds.feedburner.com/TechCrunch',
    'https://www.theverge.com/rss/index.xml'
]