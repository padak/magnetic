# Magnetic - Multi-Agent Trip Planning System

Magnetic is a sophisticated trip planning system using multi-agent architecture with Magentic-One framework integration. It helps users plan and organize their trips with AI-driven recommendations and comprehensive itineraries.

## Features

- **Multi-Agent Architecture**: Orchestrator, WebSurfer, and FileSurfer agents working together
- **Trip Planning**: Create detailed trip itineraries with activities, accommodations, and budgets
- **Document Generation**: Generate travel guides, itineraries, and emergency information
- **Real-Time Monitoring**: Monitor weather, flight status, and other travel-related information
- **Multiple LLM Support**: Use OpenAI, Anthropic, or Azure OpenAI models

## Getting Started

### Prerequisites

- Python 3.9+
- PostgreSQL
- Redis
- Node.js and npm (for frontend)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/magnetic.git
   cd magnetic
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install backend dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Playwright dependencies:
   ```bash
   playwright install --with-deps chromium
   ```

5. Install frontend dependencies:
   ```bash
   cd frontend
   npm install
   cd ..
   ```

6. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

7. Initialize the database:
   ```bash
   alembic upgrade head
   ```

### Running the Application

1. Start the backend server:
   ```bash
   uvicorn src.magnetic.api.main:app --reload
   ```

2. Start the frontend development server:
   ```bash
   cd frontend
   npm run dev
   ```

3. Access the application at http://localhost:5173

## Using Different LLM Providers

Magnetic supports multiple LLM providers. You can configure which provider to use in the `.env` file:

### OpenAI

```
LLM_PROVIDER=openai
OPENAI_API_KEY=your-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo-0125
```

### Anthropic

```
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key
ANTHROPIC_MODEL=claude-3-sonnet-20240229
```

### Azure OpenAI

```
LLM_PROVIDER=azure
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com
AZURE_DEPLOYMENT_NAME=your-deployment-name
AZURE_API_VERSION=2023-05-15
```

### Testing LLM Providers

You can test different LLM providers using the provided script:

```bash
python scripts/test_llm_providers.py --provider openai
```

Options for `--provider` are: `openai`, `anthropic`, `azure`, or `all` to test all providers.

## Project Structure

- `src/magnetic/`: Backend code
  - `agents/`: Agent implementations
  - `api/`: FastAPI endpoints
  - `config/`: Configuration
  - `models/`: Database models
  - `services/`: Business logic
  - `templates/`: Document templates
  - `utils/`: Utility functions
- `frontend/`: React frontend
  - `src/`: Frontend source code
  - `public/`: Static assets
- `scripts/`: Utility scripts
- `docs/`: Documentation
- `tests/`: Test suite

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Magnetic-One framework for AI agent capabilities
- FastAPI for the backend framework
- React and Material-UI for the frontend
- All contributors and maintainers

## 📞 Support

For support, please open an issue in the GitHub repository or contact the maintainers. 