# LinkedIn Content Automation System

Transform your GitHub projects into engaging LinkedIn posts with AI-powered content generation.

## Features

- **GitHub Repository Analysis**: Extract tech stack, features, and README content
- **Project Insights**: Auto-detect strengths, highlights, and considerations (AI integrations, deployment platforms, architecture patterns)
- **Multi-Provider AI Generation**: Generate posts using Claude, OpenAI, or Gemini
- **AI Image Generation**: Create professional visuals using Gemini 3 Pro Image (Nano Banana Pro)
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

## Project Insights

The Project Insights feature automatically analyzes repositories and generates reader-friendly insights categorized into three types:

### Insight Categories

| Category | Color | Description |
|----------|-------|-------------|
| **Strengths** | Green | What makes the project well-designed (deployment, architecture, monitoring) |
| **Highlights** | Blue | Notable integrations and capabilities (AI, payments, real-time features) |
| **Considerations** | Amber | Areas to note or potential improvements |

### Detection Categories

| Category | Examples |
|----------|----------|
| Platform & Deployment | Vercel, Netlify, AWS, Docker, Railway, Supabase, Firebase |
| Third-Party Services | Stripe, Auth0, Clerk, SendGrid, Twilio, Sentry, Analytics |
| AI & Machine Learning | OpenAI, Claude, LangChain, Vector DBs, Hugging Face |
| Architecture Patterns | Monorepo, GraphQL, tRPC, Event-driven, Serverless |
| User Experience | Real-time, PWA, i18n, Dark Mode, Accessibility, Animations |
| Data & Storage | PostgreSQL, MongoDB, Redis, S3, PlanetScale |
| Business Model | SaaS patterns, Multi-tenant, Admin Dashboard, API-first |

### Consideration Detection

Automatically detects potential gaps:
- No authentication detected
- No database found
- No deployment configuration

## AI Image Generation

### Model
Uses **Gemini 3 Pro Image** (`gemini-3-pro-image-preview`) - also known as "Nano Banana Pro" - for high-quality LinkedIn post images.

### Supported Dimensions
| Format | Dimensions | Aspect Ratio | Use Case |
|--------|------------|--------------|----------|
| Link Post (default) | 1200x627 | 16:9 | Standard link preview |
| Square | 1080x1080 | 1:1 | Engagement posts |
| Large Square | 1200x1200 | 1:1 | Detailed visuals |

### Image Styles
12 professionally designed styles:

| Style | Description | Mood |
|-------|-------------|------|
| **Infographic** | Clean data visualization layouts | Informative, educational |
| **Minimalist** | Ample negative space, focused | Elegant, sophisticated |
| **Conceptual** | Metaphorical imagery, creative | Thought-provoking |
| **Abstract** | Flowing shapes, fluid gradients | Innovative, artistic |
| **Photorealistic** | 3D rendering, cinematic lighting | Authentic, professional |
| **Illustrated** | Stylized elements, artistic texture | Friendly, approachable |
| **Diagram** | Flowcharts, connection lines | Technical, systematic |
| **Gradient** | Smooth color transitions, glassmorphism | Modern, dynamic |
| **Flat Design** | Bold geometric shapes, solid colors | Modern, clean |
| **Isometric** | 3D isometric illustration, 30° angles | Technical, dimensional |
| **Tech Themed** | Premium 3D, glassmorphism, neon accents | Innovative, cutting-edge |
| **Professional** | Corporate design, refined imagery | Trustworthy, professional |

### How It Works

1. **Content Analysis**: Analyzes your post for themes, technologies, and keywords
2. **Style Recommendation**: AI recommends optimal visual style based on content type
3. **Prompt Generation**: Builds a Gemini-optimized prompt with:
   - Scene composition (layout, background, foreground)
   - Text rendering (headline + subtitle extracted from post)
   - Aesthetic & color palette (tech-specific hex codes)
   - Context alignment
4. **Image Generation**: Gemini generates high-conversion LinkedIn visuals

### Style Recommendation Logic

The "Recommended based on content" feature analyzes your post and suggests optimal image styles. Styles marked with an "AI" badge in the UI are recommendations.

#### Content Type Classification

Posts are classified into 6 content types:

| Content Type | Description | Example Post Topics |
|--------------|-------------|---------------------|
| Tutorial | Step-by-step guides, how-tos | "How to deploy with Docker", "Setting up CI/CD" |
| Announcement | Product launches, releases | "Introducing v2.0", "New feature alert" |
| Tips | Quick insights, best practices | "5 tips for better APIs", "Lessons learned" |
| Story | Personal narratives, journeys | "My journey to senior engineer", "How we scaled" |
| Technical | Architecture, deep dives | "System design breakdown", "Performance optimization" |
| Career | Professional growth, hiring | "We're hiring!", "Career advice" |

#### Content Type → Style Mapping

Each content type has recommended styles (in priority order):

| Content Type | Recommended Styles |
|--------------|-------------------|
| Tutorial | Infographic, Minimalist, Conceptual, Diagram, Illustrated |
| Announcement | Gradient, Abstract, Minimalist, Professional, Flat Design |
| Tips | Flat Design, Minimalist, Infographic, Illustrated, Conceptual |
| Story | Photorealistic, Illustrated, Abstract, Gradient, Conceptual |
| Technical | Diagram, Isometric, Tech Themed, Minimalist, Conceptual |
| Career | Professional, Minimalist, Gradient, Flat Design, Photorealistic |

#### Technology → Style Influence

Detected technologies in your post can influence style recommendations:

| Technology Category | Technologies | Influenced Styles |
|--------------------|--------------|-------------------|
| Cloud/DevOps | AWS, Azure, GCP, Docker, Kubernetes | Isometric, Diagram |
| AI/ML | TensorFlow, PyTorch, LangChain, OpenAI | Abstract, Conceptual |
| Web Frameworks | React, Vue, Angular, Next.js | Flat Design, Tech Themed |
| Backend | Java, Spring, .NET | Professional, Diagram |
| Databases | PostgreSQL, MongoDB, Redis | Diagram, Isometric |

#### User Selection Override

- If you select a style manually, your selection is used (overrides recommendation)
- If no style is selected, the first recommended style is used automatically
- Recommendations are shown with "AI" badges in the UI for guidance

### Prompt Structure

```
**Role:** Expert LinkedIn Visual Designer
**Task:** Create a high-conversion image for a link post (1200x627).

**1. SCENE COMPOSITION:**
- Background: [context-aware with tech elements]
- Foreground: [focal point representing topic]

**2. TEXT RENDERING:**
- Headline: "[extracted from post]"
- Sub-text: "[keywords]"

**3. AESTHETIC & COLOR:**
- Style: [selected style]
- Palette: Deep background (#hex) with accent (#hex)
- Mood: [professional mood]

**4. CONTEXT:**
The post is about: [summary]
```

### Tech-Specific Color Palettes
Auto-detects technologies and applies brand colors:
- **AWS**: #FF9900 / #232F3E
- **Python**: #3776AB / #FFD43B
- **React**: #61DAFB / #282C34
- **Docker**: #2496ED / #003F8C
- And 30+ more...

## License

MIT
