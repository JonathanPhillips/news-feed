#!/usr/bin/env python3
"""
Script to set up initial category preferences.
"""
import requests
import json

API_URL = "http://localhost:8000"

# Define initial preferences
preferences = [
    {
        "category": "sports",
        "keywords": ["Atlanta Braves", "Braves", "Atlanta Falcons", "Falcons", "Georgia Bulldogs", "UGA football", "Georgia football", "Bulldogs football"],
        "priority": 1.5  # Higher priority for your favorite teams
    },
    {
        "category": "fashion", 
        "keywords": ["Take Ivy", "Ametora", "Japanese Americana", "vintage clothing", "vintage fashion", "Ivy style", "preppy style", "workwear", "heritage brands", "selvedge denim", "raw denim"],
        "priority": 1.5
    }
]

def setup_preferences():
    """Set up category preferences via API."""
    for pref in preferences:
        try:
            response = requests.post(
                f"{API_URL}/preferences",
                json=pref
            )
            if response.status_code == 200:
                print(f"✅ Set preference for {pref['category']}: {', '.join(pref['keywords'][:3])}...")
            else:
                print(f"❌ Failed to set preference for {pref['category']}: {response.text}")
        except Exception as e:
            print(f"❌ Error setting preference for {pref['category']}: {e}")

if __name__ == "__main__":
    print("Setting up category preferences...")
    setup_preferences()
    print("\nDone! Now refresh your feeds to see articles matching your preferences.")