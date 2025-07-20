# AI-Powered News Feed Desktop App

An intelligent news reader that learns your preferences and filters content using local AI.

## Project Overview

**Problem:** Traditional RSS readers like Feedly have poor signal-to-noise ratio (80-90% unwanted content) and require manual feed management.

**Solution:** AI-powered desktop app with:
- Local content filtering using LM Studio
- Automatic source discovery
- Smart categorization and trending
- Privacy-focused (all AI processing local)
- Political bias detection and analysis
- Custom topic preferences per category

## Tech Stack

- **Frontend:** HTML/CSS/JavaScript (Tauri planned for future)
- **Backend:** Python FastAPI
- **AI/ML:** LM Studio (local LLM)
- **Database:** SQLite with embeddings
- **Content Sources:** RSS feeds
- **Deployment:** Docker & Docker Compose

## Key Features

### Implemented Features ✅
- **Smart Categorization:** Auto-categorize articles (technology, politics, business, science, health, sports, entertainment, fashion, world)
- **Political Bias Detection:** -1.0 to 1.0 scale with confidence levels and detailed reasoning
- **AI Summaries:** On-demand article summarization
- **Custom Preferences:** Keyword-based topic boosting per category
- **Sentiment Analysis:** Positive/negative/neutral detection
- **Importance Scoring:** High/medium/low priority
- **User Interactions:** Like/dislike feedback system
- **Docker Deployment:** Containerized for stability

### Planned Features 📋
- **Source Discovery:** Suggest new RSS feeds based on preferences
- **Similarity Clustering:** Group duplicate stories
- **Tauri Desktop App:** Native desktop application
- **Offline Mode:** Download articles for later reading
- **Advanced Analytics:** Reading pattern insights

## Development Commands

### Local Development
```bash
# Install Python dependencies
pip install --user -r requirements.txt

# Run backend server
export PATH="/home/jon/.local/bin:$PATH"
python3 backend/main.py

# Setup initial preferences
python3 setup_preferences.py

# Open frontend
# Open src/index.html in browser or serve with:
cd src && python3 -m http.server 3000
```

### Docker Deployment (Recommended)
```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Reset database
rm -rf data/news_feed.db
docker-compose up -d
```

## Project Structure

```
news_feed/
├── backend/               # Python FastAPI backend
│   ├── ai/               # LM Studio integration
│   │   └── lm_studio_client.py
│   ├── content/          # RSS feed parsing
│   │   └── feed_parser.py
│   ├── database/         # SQLite operations
│   │   └── models.py
│   └── main.py           # FastAPI application
├── src/                  # Frontend
│   └── index.html        # Single-page application
├── data/                 # Persistent storage (created by Docker)
│   └── news_feed.db      # SQLite database
├── docker-compose.yml    # Docker orchestration
├── Dockerfile           # Backend container
├── nginx.conf           # Frontend proxy config
├── requirements.txt     # Python dependencies
├── setup_preferences.py # Initial preferences script
├── CLAUDE.md           # This file
├── README.md           # User documentation
└── DOCKER.md           # Docker documentation
```

## Development Status

### Phase 1: Basic Prototype ✅ COMPLETED
- [x] Create Python backend with LM Studio integration
- [x] Implement RSS feed fetching and parsing
- [x] Create web UI for article display
- [x] Add AI-powered content categorization
- [x] Implement basic content filtering

### Phase 2: AI Enhancement ✅ COMPLETED
- [x] Add political bias detection with reasoning
- [x] Implement content categorization (9 categories)
- [x] Add sentiment analysis
- [x] Create custom preference system
- [x] Build AI summarization feature
- [x] Add user interaction tracking

### Phase 3: Deployment & Stability ✅ COMPLETED
- [x] Docker containerization
- [x] Auto-restart on crashes
- [x] Persistent data storage
- [x] Health monitoring
- [x] Environment-based configuration

### Phase 4: Advanced Features 📋 TODO
- [ ] Tauri desktop application
- [ ] RSS feed discovery system
- [ ] Similar article clustering
- [ ] Advanced analytics dashboard
- [ ] Export/import preferences
- [ ] Multiple user profiles
- [ ] Offline reading mode
- [ ] Scheduled feed updates
- [ ] Read/unread tracking
- [ ] Archive system

## API Endpoints

### Articles
- `GET /articles` - Get filtered articles with pagination
- `GET /articles/{id}/bias-analysis` - Get detailed bias analysis
- `POST /articles/{id}/summary` - Generate AI summary
- `POST /articles/{id}/interact` - Record user interaction

### Feeds
- `GET /feeds` - Get all active RSS feeds
- `POST /feeds` - Add a new RSS feed
- `POST /refresh` - Refresh all feeds with AI processing

### Preferences
- `GET /preferences` - Get category preferences
- `POST /preferences` - Set/update preference
- `DELETE /preferences/{category}` - Delete preference

### System
- `GET /health` - Health check and LM Studio status
- `GET /` - API information

## Environment Setup

1. Install and run LM Studio: Download from https://lmstudio.ai/
2. Load any chat model in LM Studio (Llama, Mistral, etc.)
3. Start the LM Studio server (default: http://localhost:1234)
   - **For WSL users:** Make sure LM Studio server is configured to accept external connections
   - In LM Studio, go to Local Server settings and set "Enable CORS" and "Enable Network Access"
4. Install Rust: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
5. Install Tauri CLI: `cargo install tauri-cli`

### WSL Configuration
If running in WSL, the app will automatically detect the Windows host IP and connect to LM Studio running on Windows. Ensure Windows Firewall allows connections on port 1234.

## Current User Preferences

### Sports
- Atlanta Braves
- Atlanta Falcons  
- Georgia Bulldogs football

### Fashion
- Take Ivy
- Ametora
- Japanese Americana
- Vintage fashion

## Known Issues & Solutions

### Backend Crashes
- **Solution:** Use Docker deployment for auto-restart capability
- Run: `docker-compose up -d`

### LM Studio Connection (WSL)
- **Issue:** Cannot connect from WSL to Windows host
- **Solution:** Enable "Network Access" and "CORS" in LM Studio settings
- Backend auto-detects Windows host IP

### 422 Unprocessable Entity on Interactions
- **Issue:** FastAPI validation error on interaction endpoints
- **TODO:** Fix request body validation in interaction endpoint

## Notes

- All AI processing happens locally for privacy
- User preferences boost article relevance scores by 0.5
- Political bias detection includes detailed reasoning
- Docker deployment recommended for stability
- Database persists in `./data/news_feed.db`