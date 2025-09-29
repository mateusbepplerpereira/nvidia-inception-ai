# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NVIDIA Inception AI is an intelligent system for discovering and analyzing AI startups in Latin America for the NVIDIA Inception program. It uses CrewAI for agent orchestration to minimize token usage while maximizing efficiency.

## Architecture

### Core Technologies
- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **AI Orchestration**: CrewAI (only) with OpenAI GPT-4o-mini
- **Containerization**: Docker & Docker Compose
- **Web Scraping**: CrewAI Tools (no LinkedIn API)

### Project Structure
```
/backend
├── main.py                 # FastAPI application entry point
├── config.py              # Settings and environment configuration
├── agents/                # AI agent implementations
│   └── startup_crew.py    # CrewAI orchestration for startup discovery
├── app/routers/           # API endpoints
│   ├── startups.py        # Startup CRUD operations
│   ├── agents.py          # Agent task management
│   └── analysis.py        # Analysis and insights
├── database/              # Database models and connection
│   ├── models.py          # SQLAlchemy models
│   └── connection.py      # Database configuration
├── services/              # Business logic layer
│   ├── startup_service.py
│   ├── agent_service.py
│   └── analysis_service.py
└── schemas/               # Pydantic models for validation
```

## Development Commands

### Environment Setup
```bash
# Install dependencies
cd backend && pip install -r requirements.txt

# Set up environment variables
cp .env.example .env  # Edit with your OpenAI API key
```

### Running the Application
```bash
# With Docker Compose (recommended)
docker-compose up -d

# Without Docker (development)
cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Database Operations
```bash
# Create database migrations
cd backend && alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head

# Access PostgreSQL
docker exec -it nvidia_postgres psql -U nvidia_user -d nvidia_inception_db
```

### Testing
```bash
# Run tests
cd backend && pytest tests/ -v

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/api/startups
```

## Key Implementation Details

### Agent System Architecture
The system uses a **simplified agent approach** with direct OpenAI API calls for maximum token efficiency:
- **Discovery Agent**: Finds AI startups with VC funding from Latin America
- **Analysis Agent**: Scores and prioritizes startups for NVIDIA Inception
- **Market Intelligence**: Provides ecosystem insights and trends

Agent optimization for token economy:
- Direct OpenAI API calls (no complex orchestration overhead)
- Maximum 1500 tokens per request
- Temperature 0.3 for consistency
- Single-shot responses to minimize API calls
- Structured JSON responses for efficient parsing

### Database Schema
- **startups**: Core startup information with AI technologies as JSON
- **leadership**: Technical leadership with LinkedIn profiles
- **analysis**: Priority scores and strategic insights
- **agent_tasks**: Task tracking for async processing

### API Endpoints
- `GET /api/startups`: List startups with filtering
- `POST /api/agents/discover`: Trigger startup discovery
- `GET /api/analysis/dashboard`: Get aggregated insights
- `GET /api/analysis/opportunities`: Find high-priority startups

## Important Considerations

### Token Optimization
- Agents use concise prompts and limited iterations
- Sequential processing only when necessary
- Caching and database storage to avoid repeated API calls

### Data Sources
The system leverages AI knowledge and can be extended with:
- **AI-powered research**: GPT-4o-mini knowledge of Latin American startups
- **Optional integrations**: Crunchbase API, public startup databases
- **Public sources**: Company websites, GitHub profiles (CTO discovery)
- **No complex web scraping**: Simplified approach for reliability

### Startup Prioritization
Startups are scored based on:
- Technology alignment with NVIDIA ecosystem (GPU/AI usage)
- Market opportunity and sector potential
- Team strength and technical leadership
- Venture capital validation

## Environment Variables

Required in `.env`:
- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `OPENAI_MODEL`: Model to use (default: gpt-4o-mini)
- Database credentials (auto-configured with Docker)

Optional:
- `SERPER_API_KEY`: For enhanced web search capabilities

## Troubleshooting

### Common Issues
1. **Import errors**: Ensure all dependencies are installed
2. **Database connection**: Check Docker containers are running
3. **API rate limits**: Adjust agent iterations and delays

### Debugging
```bash
# Check container logs
docker-compose logs backend
docker-compose logs postgres

# Interactive Python shell
docker exec -it nvidia_backend python
>>> from agents.startup_crew import StartupDiscoveryCrew
>>> crew = StartupDiscoveryCrew()
```

## Next Steps for Development

1. **Enhanced Data Sources**: Integrate more startup databases and APIs
2. **Improved Analysis**: Add ML models for better scoring
3. **Notification System**: Weekly reports to NVIDIA team
4. **Dashboard UI**: React frontend for visualization
5. **Batch Processing**: Schedule regular discovery tasks