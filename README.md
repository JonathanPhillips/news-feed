# AI News Feed

An intelligent desktop news aggregation application that uses local AI to filter, categorize, and analyze news content with political bias detection.

## Features

🤖 **AI-Powered Content Analysis**
- Automatic article categorization (technology, politics, business, science, health, sports, entertainment, world)
- Sentiment analysis (positive, negative, neutral)
- Importance scoring (high, medium, low)
- Topic extraction and tagging

🎯 **Political Bias Detection**
- Bias scoring on a -1.0 to 1.0 scale (left to right)
- Confidence levels for bias assessments
- Detailed reasoning explaining AI's bias determination
- Visual bias indicators with color-coded scales

📊 **Smart Content Discovery**
- RSS feed parsing and management
- Relevance scoring based on user preferences
- AI-generated summaries on demand
- User interaction tracking for personalization

🔒 **Privacy-Focused**
- Local AI processing with LM Studio
- No external API calls for content analysis
- Local SQLite database storage

## Architecture

- **Frontend**: HTML/CSS/JavaScript with responsive design
- **Backend**: Python FastAPI server
- **Database**: SQLite with embedding storage
- **AI**: LM Studio (local LLM) for content analysis
- **Future**: Tauri desktop app framework

## Setup

### Prerequisites

- Python 3.8+
- LM Studio running locally
- WSL2 (if on Windows)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd news_feed
```

2. Install Python dependencies:
```bash
pip install --user fastapi uvicorn feedparser requests openai==0.28.1 numpy
```

3. Set up LM Studio:
   - Install and run LM Studio
   - Load a model (e.g., Mistral 7B Instruct)
   - Enable "Network Access" and "Enable CORS" in settings
   - Ensure it's running on port 1234

4. Initialize the database:
```bash
python3 backend/main.py
```

## Usage

### Starting the Application

1. Start the backend server:
```bash
export PATH="/home/jon/.local/bin:$PATH"
python3 backend/main.py
```

2. Open the frontend:
```bash
# Open src/index.html in your browser
# Or serve it locally:
cd src
python3 -m http.server 3000
```

3. Access the application at `http://localhost:3000`

### Using the Interface

- **Refresh Feeds**: Click "🔄 Refresh Feeds" to fetch new articles
- **Filter by Category**: Use the dropdown to filter articles by category
- **AI Summary**: Click "🤖 AI Summary" on any article for an AI-generated summary
- **Bias Analysis**: Click "🎯 Bias Analysis" on political articles to see detailed bias assessment
- **Read Full Article**: Click "Read Full" to open the original article
- **Rate Articles**: Use 👍/👎 buttons to help train the relevance algorithm

## Configuration

### Adding RSS Feeds

Default feeds are automatically added on first run. To add custom feeds:

```bash
curl -X POST "http://localhost:8000/feeds" \
  -H "Content-Type: application/json" \
  -d '{"feed_url": "https://example.com/rss"}'
```

### LM Studio Configuration

For WSL users, the application automatically detects the Windows host IP. If you're running everything locally, it will use `localhost:1234`.

Manual configuration in `backend/ai/lm_studio_client.py`:
```python
self.base_url = "http://your-lm-studio-host:1234"
```

## API Endpoints

- `GET /` - API information and health status
- `GET /articles` - Get filtered articles with pagination
- `GET /feeds` - Get all active RSS feeds
- `POST /feeds` - Add a new RSS feed
- `POST /refresh` - Refresh all feeds and process with AI
- `POST /articles/{id}/summary` - Generate AI summary for article
- `GET /articles/{id}/bias-analysis` - Get detailed bias analysis
- `POST /articles/{id}/interact` - Record user interaction
- `GET /health` - Health check and LM Studio status

## Database Schema

### Articles Table
- Basic metadata (title, URL, content, author, published date)
- AI analysis results (category, sentiment, importance, topics)
- Political bias data (bias score, confidence, reasoning)
- User interaction data (relevance score)
- Vector embeddings for similarity matching

### Feeds Table
- RSS feed metadata and management
- Active/inactive status and last fetch times

### User Interactions Table
- Tracks user behavior (views, likes, dislikes, read time)
- Used for personalization and relevance scoring

## Development

### Project Structure
```
news_feed/
├── backend/
│   ├── ai/
│   │   └── lm_studio_client.py    # LM Studio integration
│   ├── content/
│   │   └── feed_parser.py         # RSS parsing
│   ├── database/
│   │   └── models.py              # Database operations
│   └── main.py                    # FastAPI application
├── src/
│   └── index.html                 # Frontend application
├── CLAUDE.md                      # Project documentation
└── README.md                      # This file
```

### Running Tests

Currently no automated tests. Manual testing via the web interface.

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Troubleshooting

### Backend Issues

**"Backend Offline" status**:
- Check if the Python server is running on port 8000
- Verify no port conflicts: `lsof -i:8000`

**"AI Offline" status**:
- Ensure LM Studio is running and has a model loaded
- Check LM Studio settings: Enable "Network Access" and "Enable CORS"
- For WSL: Verify Windows firewall allows port 1234

**Database errors**:
- Run the migration script: `python3 add_bias_reasoning_column.py`
- Delete `news_feed.db` to reset (will lose data)

### Frontend Issues

**"Loading articles..." stuck**:
- Restart the backend server
- Check browser console for JavaScript errors
- Verify API endpoints are responding: `curl http://localhost:8000/health`

**Bias analysis not working**:
- Ensure articles have been processed with AI (refresh feeds)
- Check that LM Studio is available and responding

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- LM Studio for local AI processing
- FastAPI for the backend framework
- RSS feed providers for content sources