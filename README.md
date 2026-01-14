# LinkedIn Content Automation System

Transform your GitHub projects into engaging LinkedIn posts with AI-powered content generation.

## Features

- **GitHub Repository Analysis**: Extract tech stack, features, and README content
- **Multi-Provider AI Generation**: Generate posts using Claude, OpenAI, or Gemini
- **AI Image Generation**: Create accompanying visuals for your posts
- **3 Post Styles**:
  - Problem-Solution: Present your project as the solution to a relatable problem
  - Tips & Learnings: Share key insights and lessons learned
  - Technical Showcase: Highlight architecture and tech decisions
- **Secure API Key Management**: Client-side encrypted key storage with session expiry
- **Rate Limiting & Security**: Built-in rate limiting and security headers

## Tech Stack

### Backend
- Python 3.11+ with FastAPI
- Multi-provider AI: Anthropic Claude, OpenAI, Google Gemini
- PyGithub for repository analysis
- Cryptography for secure key handling
- Session management with automatic cleanup

### Frontend
- React 19 + TypeScript + Vite
- Tailwind CSS + Shadcn/ui + Radix UI
- React Query + Zustand for state management
- Framer Motion for animations

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- npm

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn src.api.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

## Usage

1. Open the dashboard at http://localhost:5173
2. Connect your preferred AI provider (Claude, OpenAI, or Gemini) with your API key
3. Enter a GitHub repository URL
4. Click "Analyze" to extract project information
5. Choose between:
   - **AI Generation**: Generate posts directly using connected AI provider
   - **Prompt Templates**: Copy prompts for manual use with Claude Code CLI
6. Optionally generate an accompanying image
7. Copy and post to LinkedIn

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze` | POST | Analyze a GitHub repository |
| `/api/generate` | POST | Generate a LinkedIn post prompt |
| `/api/templates` | GET | List available post styles |
| `/api/claude/*` | - | Claude AI provider routes |
| `/api/openai/*` | - | OpenAI provider routes |
| `/api/gemini/*` | - | Gemini provider routes |
| `/api/images/*` | - | Image generation routes |

## Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# GitHub (optional, for private repos)
GITHUB_TOKEN=your_github_token

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# Environment (development/production)
ENVIRONMENT=development

# Rate Limiting (requests per minute)
RATE_LIMIT_AUTH=100
RATE_LIMIT_GENERATION=20

# Production frontend URL (for CORS)
FRONTEND_URL=https://your-domain.com
```

## Project Structure

```
linkedin-content-automation/
├── backend/
│   ├── src/
│   │   ├── api/           # FastAPI routes (main, claude, openai, gemini, image)
│   │   ├── analyzers/     # GitHub analysis modules
│   │   ├── generators/    # Prompt generation
│   │   ├── middleware/    # Rate limiting, security headers, sessions
│   │   ├── models/        # Pydantic schemas
│   │   ├── services/      # AI clients, encryption, session management
│   │   ├── tasks/         # Background cleanup tasks
│   │   ├── utils/         # Utility functions
│   │   └── validators/    # Input validation
│   ├── prompts/           # Post templates (problem_solution, tips_learnings, technical_showcase)
│   ├── tests/             # Test suite
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── analysis/      # Repository analysis display
│   │   │   ├── layout/        # Header, layout components
│   │   │   ├── legal/         # Terms & Privacy modals
│   │   │   ├── posts/         # Post generation & preview
│   │   │   ├── providers/     # AI provider connection panel
│   │   │   ├── repo-input/    # Repository URL input
│   │   │   └── ui/            # Shadcn/ui components
│   │   ├── hooks/         # Custom React hooks
│   │   ├── lib/           # API client
│   │   └── store/         # Zustand state management
│   └── package.json
└── README.md
```

## Security

- API keys are encrypted client-side before transmission
- Session-based key storage with automatic expiry
- Rate limiting protects against abuse
- Security headers (CSP, XSS protection, etc.)
- No API keys stored on server permanently

## License

MIT
