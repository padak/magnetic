# Technical Architecture and Technology Stack

## Implementation Status

### ✅ Implemented
- Basic project structure
- Virtual environment setup
- Core dependencies installation
- Basic configuration system
- Documentation framework

### 🔄 In Progress
- Environment variable configuration
- Database setup
- Testing framework

### 📅 Planned
- Agent implementation
- API integrations
- Storage systems
- Security features

## Core Framework
- **Magentic-One Framework**: Built on autogen-agentchat for multi-agent orchestration
  - Version: Latest stable release
  - Primary Model: GPT-4o for optimal reasoning capabilities
  - Dependencies: `autogen-agentchat`, `autogen-ext[magentic-one,openai]`

## Project Structure
```
magnetic/
├── docs/                    # Project documentation
│   ├── project_scope.md     # Project scope and features
│   ├── technical_architecture.md
│   ├── architecture_diagrams.md
│   └── work_plan.md        # Development timeline and tasks
├── src/
│   └── magnetic/
│       ├── agents/         # Agent implementations
│       ├── core/          # Core functionality
│       ├── utils/         # Utility functions
│       ├── models/        # Data models
│       ├── services/      # Business logic
│       ├── config/        # Configuration
│       │   └── settings.py
│       └── __init__.py
├── tests/                  # Test suite
├── venv/                   # Virtual environment
├── .gitignore
└── requirements.txt        # Project dependencies
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

### 1. Storage (Planned)
- **Local Storage**:
  - SQLite: For development
  - PostgreSQL: For production
- **Caching**:
  - Redis: For session data and API responses
- **File Storage**:
  - Local filesystem (development)
  - S3-compatible storage (production)

### 2. Data Models (To Be Implemented)
```python
# Core data structures (example)
class TripPlan:
    id: str
    user_preferences: Dict[str, Any]
    itinerary: List[DayPlan]
    budget: Budget
    documents: List[Document]

class DayPlan:
    date: datetime
    activities: List[Activity]
    accommodations: Accommodation
    transportation: List[Transport]

class Budget:
    total: Decimal
    breakdown: Dict[str, Decimal]
    currency: str
```

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
- `pytest-asyncio`: For async testing
- `pytest-cov`: For coverage reporting

### 3. Documentation
- Sphinx: For API documentation (planned)
- MkDocs: For user documentation (planned)

## Dependencies Installation
```bash
# Core dependencies
pip install -r requirements.txt
playwright install --with-deps chromium
```

## Configuration Management
Environment variables will be managed through `.env` files:

```bash
# .env.example
OPENAI_API_KEY=your-api-key
AMADEUS_API_KEY=your-amadeus-key
MAPS_API_KEY=your-maps-key
WEATHER_API_KEY=your-weather-key

# Database
DATABASE_URL=sqlite:///./magnetic.db

# Redis
REDIS_URL=redis://localhost:6379/0

# Agent Settings
MODEL_NAME=gpt-4o
```

This technical architecture document serves as a blueprint for development and will be updated as the project evolves. All version numbers should be regularly reviewed and updated to maintain security and compatibility. 