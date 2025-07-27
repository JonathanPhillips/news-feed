#!/usr/bin/env python3
"""Check for miscategorized articles."""

import requests
import json

def check_categorization():
    """Check for articles that should be sports or fashion but aren't."""
    try:
        response = requests.get("http://localhost:8000/articles?limit=100")
        data = response.json()
        
        print("🔍 ANALYZING ARTICLE CATEGORIZATION:")
        print("="*50)
        
        sports_keywords = ['sport', 'football', 'basketball', 'baseball', 'soccer', 'tennis', 'golf', 'team', 'player', 'game', 'match', 'league']
        fashion_keywords = ['fashion', 'style', 'designer', 'clothing', 'runway', 'trend', 'wear', 'dress', 'outfit']
        
        miscat_sports = []
        miscat_fashion = []
        
        for article in data['articles']:
            title = article['title'].lower()
            category = article['category']
            topics = str(article.get('topics', [])).lower()
            url = article.get('url', '')
            
            # Skip our sample articles
            if 'example.com' in url:
                continue
                
            # Check for sports content
            has_sports = any(keyword in title or keyword in topics for keyword in sports_keywords)
            has_fashion = any(keyword in title or keyword in topics for keyword in fashion_keywords)
            
            if has_sports and category != 'sports':
                miscat_sports.append({
                    'title': article['title'],
                    'category': category,
                    'topics': article.get('topics', [])
                })
                
            if has_fashion and category != 'fashion':
                miscat_fashion.append({
                    'title': article['title'], 
                    'category': category,
                    'topics': article.get('topics', [])
                })
        
        print(f"\n❌ SPORTS ARTICLES MISCATEGORIZED ({len(miscat_sports)} found):")
        for article in miscat_sports:
            print(f"  Title: {article['title']}")
            print(f"  Categorized as: {article['category']}")
            print(f"  Topics: {article['topics']}")
            print()
            
        print(f"❌ FASHION ARTICLES MISCATEGORIZED ({len(miscat_fashion)} found):")
        for article in miscat_fashion:
            print(f"  Title: {article['title']}")
            print(f"  Categorized as: {article['category']}")
            print(f"  Topics: {article['topics']}")
            print()
            
        print(f"SUMMARY:")
        print(f"  - {len(miscat_sports)} sports articles miscategorized")
        print(f"  - {len(miscat_fashion)} fashion articles miscategorized")
        
        # Also check category distribution
        categories = {}
        for article in data['articles']:
            if 'example.com' not in article.get('url', ''):
                cat = article['category']
                categories[cat] = categories.get(cat, 0) + 1
                
        print(f"\nREAL ARTICLE CATEGORY DISTRIBUTION:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"  {cat}: {count}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_categorization()