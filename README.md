# US Family Trip Planner

A comprehensive travel planning system built with Python, FastAPI, and React, using Magnetic-One's multi-agent architecture for intelligent trip planning.

## 🌟 Features

- **Intelligent Trip Planning**: Utilizes AI agents to create personalized travel itineraries
- **Multi-Agent Architecture**: Leverages specialized agents for different aspects of trip planning
  - Orchestrator Agent: Coordinates planning activities
  - WebSurfer Agent: Gathers real-time travel information
  - FileSurfer Agent: Manages document processing
- **Real-Time Data Integration**:
  - Weather forecasts
  - Flight availability
  - Hotel pricing
  - Local attractions
- **Family-Focused Planning**:
  - Age-appropriate activities
  - Family-friendly accommodations
  - Accessible transportation options
  - Budget management

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- Docker and Docker Compose
- PostgreSQL
- Redis

### Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/magnetic.git
cd magnetic
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
playwright install --with-deps chromium
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

### Database Setup

1. Start the Docker containers:
```bash
docker-compose up -d
```

2. Run database migrations:
```bash
alembic upgrade head
```

### Running the Application

1. Start the backend server:
```bash
uvicorn magnetic.api.main:app --reload
```

2. Start the frontend development server:
```bash
cd frontend/magnetic-ui
npm install
npm run dev
```

## 🏗️ Project Structure

```
magnetic/
├── src/
│   └── magnetic/
│       ├── agents/         # AI agent implementations
│       ├── api/           # FastAPI application
│       ├── config/        # Configuration management
│       ├── models/        # Database models
│       ├── services/      # Business logic services
│       └── utils/         # Utility functions
├── frontend/
│   └── magnetic-ui/      # React frontend application
├── tests/                # Test suite
├── docs/                 # Documentation
├── migrations/           # Database migrations
└── scripts/             # Utility scripts
```

## 🔧 Configuration

The application uses several external APIs:
- OpenAI API for AI capabilities
- Amadeus API for travel data
- Google Maps API for location services
- Open-Meteo API for weather forecasts

Configure these in your `.env` file.

## 🧪 Testing

Run the test suite:
```bash
pytest
```

Test API integrations:
```bash
python scripts/test_apis.py
```

## 📚 Documentation

- API documentation is available at `/docs` when running the server
- Additional documentation can be found in the `docs/` directory

## 🛠️ Development

1. Create a new branch for your feature:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and commit:
```bash
git add .
git commit -m "Add your feature"
```

3. Push your changes:
```bash
git push origin feature/your-feature-name
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Magnetic-One framework for AI agent capabilities
- FastAPI for the backend framework
- React and Material-UI for the frontend
- All contributors and maintainers

## 📞 Support

For support, please open an issue in the GitHub repository or contact the maintainers. 