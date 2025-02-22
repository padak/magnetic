# US Family Trip Planner System Description

## Overview
The US Family Trip Planner is an intelligent travel planning system that uses a multi-agent architecture to help families plan and organize their trips within the United States. The system combines web scraping, API integrations, and AI-driven planning to create comprehensive travel itineraries.

## System Architecture

### Core Components

#### 1. Frontend (React + TypeScript)
- Modern React application using TypeScript
- Chakra UI for consistent and accessible design
- React Router for navigation
- React Query for state management
- Form handling with React Hook Form
- Responsive design for all devices

#### 2. Backend (FastAPI + PostgreSQL)
- FastAPI application with async support
- PostgreSQL database with SQLAlchemy ORM
- Alembic for database migrations
- Redis for caching and state management
- Comprehensive API documentation with OpenAPI

#### 3. Agent System

##### WebSurfer Agent (Completed)
A sophisticated web interaction agent responsible for:
- Web scraping using Playwright
- API integrations:
  - Google Maps for route planning and location services
  - Open-Meteo for weather data
  - Amadeus for flight and hotel information
- Features:
  - Intelligent route optimization
  - Real-time weather monitoring
  - Flight tracking
  - Hotel search and comparison
  - Attraction recommendations
- Robust error handling and resource management
- Comprehensive test coverage

##### Orchestrator Agent (In Progress)
Manages and coordinates other agents:
- Task distribution and prioritization
- State management
- Error handling and recovery
- Performance monitoring

##### Future Agents (Planned)
- FileSurfer Agent for document management
- Coder Agent for data processing and analysis

### Data Models

#### Trip
- Basic information (title, description, dates)
- Destination and preferences
- Status tracking
- Budget information
- Itinerary days and activities

#### Additional Models
- ItineraryDay
- Activity
- Accommodation
- Budget

## Key Features

### Implemented
1. Trip Management
   - Creation, reading, updating, and deletion
   - Status tracking
   - Preference management

2. Route Planning
   - Intelligent route optimization
   - Multiple route alternatives
   - Traffic and toll information
   - Waypoint handling

3. Travel Research
   - Weather information
   - Location details
   - Flight options
   - Hotel availability and pricing

### In Development
1. Document Generation
   - Itinerary PDFs
   - Travel guides
   - Emergency information

2. Advanced Planning
   - AI-driven recommendations
   - Dynamic optimization
   - Budget management

## Technical Details

### Development Environment
- Python 3.13
- Node.js with TypeScript
- Docker containers
- Virtual environment management

### Testing
- Comprehensive test suite for WebSurfer agent
- Integration tests for API endpoints
- Frontend component testing
- Mock implementations for external services

### Security
- API key management
- Error handling
- Input validation
- Resource cleanup

## Future Roadmap
1. Enhanced agent collaboration
2. Machine learning integration
3. Mobile application
4. Social features
5. Real-time updates
6. Booking integration

## Documentation
- API documentation (OpenAPI)
- Component documentation
- Testing documentation
- Deployment guides

## Implementation Details

### WebSurfer Agent (Magentic-One)

The WebSurfer agent has been enhanced with Magentic-One integration, providing:

1. **Task Structure**
   ```python
   {
       'type': 'task_type',  # e.g., 'weather', 'location_search'
       'required_info': ['field1', 'field2'],  # Required information
       'params': {...}  # Task-specific parameters
   }
   ```

2. **Core Capabilities**
   - Web scraping with CSS selectors
   - Weather information retrieval
   - Location search and details
   - Travel search and booking
   - Route planning with preferences
   - Destination research

3. **Integration Features**
   - OpenAI GPT-4 for natural language understanding
   - Playwright for reliable web automation
   - Structured responses for consistent data format
   - Error handling and recovery mechanisms

4. **Example Usage**
   ```python
   # Initialize WebSurfer
   websurfer = WebSurferM1()
   await websurfer.initialize()

   # Get weather information
   weather = await websurfer.get_weather("San Francisco")

   # Research a destination
   info = await websurfer.research_destination(
       destination="Boston",
       dates={"arrival": "2024-04-01", "departure": "2024-04-05"},
       preferences={"budget": "medium", "interests": ["history", "food"]}
   )
   ```

## Future Enhancements

1. **Planned Migrations**
   - FileSurfer Agent to Magentic-One
   - Integration testing framework
   - Performance monitoring

2. **New Features**
   - Enhanced error recovery
   - Parallel task execution
   - Caching and rate limiting
   - More specialized agents

## Dependencies

- autogen-ext[magentic-one,openai]>=0.2.0
- playwright for web automation
- pytest for testing
- Other core Python packages

## Configuration

The system uses environment variables for configuration:
- OPENAI_API_KEY: OpenAI API key
- Other API keys as needed

## Testing

Comprehensive test suite includes:
- Unit tests for each agent
- Integration tests for agent collaboration
- Mocked external services
- Async test support 