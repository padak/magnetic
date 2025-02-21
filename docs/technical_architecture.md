# Technical Architecture and Technology Stack

## Implementation Status

### ✅ Implemented
- Basic project structure
- Virtual environment setup
- Core dependencies installation
- Configuration system
- Logging framework
- Docker environment with PostgreSQL and Redis
- Health check endpoints
- Database models and migrations
- Base agent system
- Task management system
- Testing framework

### 🔄 In Progress
- Redis caching implementation
- WebSurfer agent development
- API endpoints creation
- File storage system

### 📅 Planned
- Authentication system
- Travel API integrations
- Document generation
- Monitoring system

## Core Framework
- **FastAPI Framework**: Modern web framework for building APIs
  - Version: 0.100+
  - Async support for high performance
  - OpenAPI documentation
  - Dependencies: `fastapi`, `uvicorn[standard]`

## Project Structure
```
magnetic/
├── docs/                    # Project documentation
├── src/
│   └── magnetic/
│       ├── agents/         # Agent implementations
│       │   ├── base.py     # Base agent class
│       │   └── orchestrator.py # Orchestrator implementation
│       ├── api/            # API endpoints
│       │   └── main.py     # FastAPI application
│       ├── core/           # Core functionality
│       ├── utils/          # Utility functions
│       │   └── logging.py  # Logging configuration
│       ├── models/         # Data models
│       │   ├── base.py     # Base model
│       │   └── trip.py     # Trip-related models
│       ├── services/       # Business logic
│       ├── config/         # Configuration
│       │   └── settings.py # Settings management
│       └── __init__.py
├── tests/                  # Test suite
│   ├── test_config.py     # Configuration tests
│   └── test_agents.py     # Agent system tests
├── scripts/               # Utility scripts
│   └── test_docker.py    # Docker environment tests
├── migrations/           # Database migrations
├── .env.example         # Environment variables template
├── requirements.txt     # Project dependencies
├── setup.py            # Package configuration
├── Dockerfile          # Container definition
└── docker-compose.yml  # Container orchestration
```

## Agent Architecture

### 1. Base Infrastructure
- **Python**: ^3.9
- **asyncio**: For asynchronous operations
- **Docker**: For containerization and isolation
- **Virtual Environment**: For dependency management

### 2. Agent-Specific Technologies

#### Orchestrator Agent
- **Framework**: autogen-agentchat MagenticOneGroupChat
- **Model**: GPT-4o for complex reasoning
- **State Management**: 
  - Task Ledger implementation
  - Progress Ledger implementation
  - JSON-based state persistence

#### WebSurfer Agent
- **Browser Automation**: Playwright
  - Chromium-based browser integration
  - `playwright-python`: ^1.40
- **Web Interaction**:
  - Accessibility tree navigation
  - Set-of-marks prompting system
- **Data Fetching**:
  - `requests`: ^2.31
  - `aiohttp`: ^3.9 for async operations
- **APIs Integration**:
  - Travel APIs (Amadeus, Skyscanner)
  - Weather APIs (OpenWeatherMap)
  - Maps APIs (Google Maps, OpenStreetMap)

#### Coder Agent
- **Development Tools**:
  - `black`: For code formatting
  - `pylint`: For code quality
  - `mypy`: For type checking
- **Data Processing**:
  - `pandas`: ^2.1
  - `numpy`: ^1.24
- **Visualization**:
  - `plotly`: ^5.18
  - `folium`: For interactive maps
  - `matplotlib`: For static visualizations

#### FileSurfer Agent
- **File Operations**:
  - `pathlib`: For path handling
  - `watchdog`: For file system monitoring
- **Document Generation**:
  - `fpdf2`: For PDF generation
  - `jinja2`: For template rendering
  - `markdown`: For markdown processing

## Data Architecture

### 1. Storage Implementation
- **Database**:
  - PostgreSQL: Primary database for all environments
  - Benefits:
    - Better concurrency support for multi-agent system
    - Native JSON support for agent state storage
    - Robust transaction handling
    - Docker-friendly deployment
- **Caching**:
  - Redis: For agent state and API response caching
  - Implementation status: Docker container ready, caching layer pending
- **File Storage**:
  - Local filesystem (development)
  - S3-compatible storage (production)
  - Implementation status: Pending

### 2. Database Schema
```python
# Core data models (Implemented)
class BaseModel(Base):
    """Base model with common fields."""
    id: Mapped[int] = Column(Integer, primary_key=True)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = Column(DateTime, onupdate=datetime.utcnow)

class Trip(BaseModel):
    """Trip model with SQLAlchemy ORM."""
    title: Mapped[str]
    description: Mapped[Optional[str]]
    start_date: Mapped[datetime]
    end_date: Mapped[datetime]
    status: Mapped[TripStatus]
    preferences: Mapped[dict] = Column(JSON)
    
    # Relationships
    itinerary_days: Mapped[List["ItineraryDay"]]
    budget: Mapped["Budget"]

# Additional models implemented:
# - ItineraryDay
# - Activity
# - Accommodation
# - Budget
```

### 3. Data Access Layer
- SQLAlchemy ORM for database operations
- Alembic for database migrations
- Connection pooling configured in Docker environment
- Health checks implemented for database monitoring

## Current Configuration System
```python
@dataclass
class Config:
    """Application configuration."""
    
    # API configurations
    api_keys: Dict[str, str]
    
    # Model configurations
    model_settings: Dict[str, Any]
    
    # Storage configurations
    storage_settings: Dict[str, Any]
    
    # Agent configurations
    agent_settings: Dict[str, Any]

    @classmethod
    def load_from_env(cls) -> 'Config':
        """Load configuration from environment variables."""
        # TODO: Implement environment variable loading
        return cls(
            api_keys={},
            model_settings={},
            storage_settings={},
            agent_settings={}
        )
```

## Security Implementation (Planned)

### 1. Environment Security
- Docker containerization
- Virtual environment isolation
- Environment variable management with `python-dotenv`

### 2. API Security
- API key management
- Rate limiting
- Request validation

### 3. Data Protection
- Input sanitization
- HTTPS enforcement
- Data encryption at rest

## Integration Points (To Be Implemented)

### 1. External Services
- Travel booking APIs
- Weather services
- Map services
- Currency exchange services

### 2. Internal Services
- Authentication service
- Logging service
- Monitoring service

## Development Workflow

### 1. Version Control
- Git
- GitHub Actions for CI/CD (planned)

### 2. Testing (To Be Implemented)
- `pytest`: For unit testing
- `