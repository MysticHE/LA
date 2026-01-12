# LinkedIn Content Automation System

Transform your GitHub projects into engaging LinkedIn posts with AI-powered content generation.

## Features

- Analyze GitHub repositories (tech stack, features, README)
- Generate LinkedIn post prompts in 3 styles:
  - Problem-Solution: Start with a relatable problem, present your project as the solution
  - Tips & Learnings: Share key insights and lessons learned
  - Technical Showcase: Highlight architecture and tech decisions
- Copy-to-clipboard for Claude Code integration
- Modern React dashboard with Shadcn/ui

## Tech Stack

### Backend
- Python 3.11+
- FastAPI
- PyGithub
- Pydantic

### Frontend
- React 19
- TypeScript
- Vite
- Tailwind CSS
- Shadcn/ui
- React Query
- Zustand

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
2. Enter a GitHub repository URL (e.g., `https://github.com/owner/repo`)
3. Click "Analyze" to extract project information
4. Select a post style from the tabs
5. Click "Copy Prompt" to copy the generated prompt
6. Open Claude Code CLI and paste the prompt
7. Review the generated LinkedIn post and make any edits
8. Copy and paste to LinkedIn

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze` | POST | Analyze a GitHub repository |
| `/api/generate` | POST | Generate a LinkedIn post prompt |
| `/api/templates` | GET | List available post styles |

## Environment Variables

Create a `.env` file in the `backend/` directory:

```
GITHUB_TOKEN=your_github_token  # Optional, for private repos
```

## Project Structure

```
linkedin-content-automation/
├── backend/
│   ├── src/
│   │   ├── api/           # FastAPI routes
│   │   ├── analyzers/     # GitHub analysis modules
│   │   ├── generators/    # Prompt generation
│   │   └── models/        # Pydantic schemas
│   ├── prompts/           # Post templates
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom hooks
│   │   ├── lib/           # API client
│   │   └── store/         # Zustand state
│   └── package.json
└── README.md
```

## License

MIT
