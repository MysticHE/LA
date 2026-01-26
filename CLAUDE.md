# LinkedIn Content Automation - Claude Code Context

## Project Overview

A full-stack application that transforms GitHub projects into engaging LinkedIn posts with AI-powered content and image generation.

## Architecture

```
linkedin-content-automation/
├── backend/          # Python FastAPI server
│   └── src/
│       ├── api/      # Route handlers
│       ├── services/ # AI clients, key storage
│       ├── generators/image_generator/  # Image prompt building
│       └── analyzers/ # Content analysis
└── frontend/         # React + TypeScript + Vite
    └── src/
        ├── components/  # UI components
        ├── store/       # Zustand state
        └── lib/         # API client
```

## Key Components

### Image Generation System

**Model**: `gemini-3-pro-image-preview` (Nano Banana Pro)

**Files**:
- `backend/src/services/gemini_client.py` - Gemini API client
- `backend/src/generators/image_generator/prompt_builder.py` - Prompt construction
- `backend/src/generators/image_generator/style_recommender.py` - Style selection
- `backend/src/api/image_routes.py` - API endpoints
- `frontend/src/components/posts/ImageGenerationPanel.tsx` - UI

**Prompt Structure** (Gemini-optimized):
```
**Role:** Expert LinkedIn Visual Designer
**Task:** Create a high-conversion image for a [dimension].

**1. SCENE COMPOSITION:**
- Background: [context with tech elements]
- Foreground: [focal point]

**2. TEXT RENDERING:**
- Headline: "[from post]"
- Sub-text: "[keywords]"

**3. AESTHETIC & COLOR:**
- Style: [selected]
- Palette: [hex codes]
- Mood: [professional]

**4. CONTEXT:**
The post is about: [summary]
```

**Supported Dimensions**:
- `1200x627` (default) - Link post, 16:9
- `1080x1080` - Square, 1:1
- `1200x1200` - Large square, 1:1

**Image Styles**: 12 styles defined in `STYLE_AESTHETICS` dict
- infographic, minimalist, conceptual, abstract
- photorealistic, illustrated, diagram, gradient
- flat_design, isometric, tech_themed, professional

**Tech Color Palettes**: 30+ technologies with hex codes in `TECH_COLOR_PALETTES`

### Content Analysis Pipeline

1. `ContentAnalyzer` - Extracts themes, technologies, keywords, sentiment
2. `ContentClassifier` - Classifies into: Tutorial, Announcement, Tips, Story, Technical, Career
3. `StyleRecommender` - Recommends image style based on content type + tech stack
4. `GeminiPromptBuilder` - Builds optimized prompt from all components

### AI Providers

- **Claude** (`/api/claude/*`) - Anthropic Claude for post generation
- **OpenAI** (`/api/openai/*`) - GPT models for post generation
- **Gemini** (`/api/gemini/*`) - Image generation + post generation

### Security

- API keys encrypted client-side, stored in session with expiry
- Rate limiting: 20 req/min for generation, 100 req/min for auth
- Input validation with size limits (10KB post, 2KB prompt)

## Development Commands

### Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn src.api.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## Code Conventions

### Backend (Python)
- FastAPI with Pydantic models
- Async/await for API calls
- Type hints required
- Dataclasses for internal data structures
- Services follow singleton pattern with `get_*()` functions

### Frontend (TypeScript)
- React 19 with hooks
- Zustand for global state
- React Query for server state
- Shadcn/ui + Radix for components
- Tailwind CSS for styling

## Common Tasks

### Update Image Model
Edit `backend/src/services/gemini_client.py`:
```python
DEFAULT_MODEL = "gemini-3-pro-image-preview"
```

### Add New Image Style
Edit `backend/src/generators/image_generator/prompt_builder.py`:
```python
STYLE_AESTHETICS[ImageStyle.NEW_STYLE] = {
    "style": "description",
    "mood": "mood description",
}
```

### Add Tech Color Palette
Edit `backend/src/generators/image_generator/prompt_builder.py`:
```python
TECH_COLOR_PALETTES["newtool"] = {
    "primary": "#HEX",
    "secondary": "#HEX",
    "accent": "#HEX"
}
```

### Modify Prompt Structure
Edit `_format_prompt()` in `backend/src/generators/image_generator/prompt_builder.py`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/analyze` | POST | Analyze GitHub repo |
| `/api/generate` | POST | Generate post prompt |
| `/api/generate/image` | POST | Generate image |
| `/api/auth/gemini/connect` | POST | Connect Gemini API key |
| `/api/auth/gemini/status` | GET | Check connection status |

## Environment Variables

```bash
# backend/.env
GITHUB_TOKEN=           # Optional, for private repos
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
RATE_LIMIT_GENERATION=20
FRONTEND_URL=           # For CORS in production
```

## Deployment

Deployed on Render:
- Backend: Python web service
- Frontend: Static site

See `DEPLOYMENT_GUIDE.md` for details.
