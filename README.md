# LinkedIn Content Automation System

Transform your GitHub projects into engaging LinkedIn posts with AI-powered content generation.

## Features

- **GitHub Repository Analysis**: Extract tech stack, features, and README content with AI-powered summaries
- **Project Insights**: Auto-detect strengths and considerations with merged features & highlights in a clean 2x2 grid layout
- **Multi-Provider AI Generation**: Generate posts using Claude, OpenAI, or Gemini
- **AI Image Generation**: Create professional visuals using Gemini 3 Pro Image (Nano Banana Pro)
- **3 Post Styles** (with value-first prompts):
  - Problem-Solution: Frustration-first hooks that resonate with developers
  - Tips & Learnings: Counterintuitive insights and "I was wrong about..." hooks
  - Technical Showcase: "Why I didn't use X" and trade-off discussions
- **Editable Generated Content**: Edit AI-generated posts before copying or generating images
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

## Project Analysis

The Project Analysis feature automatically analyzes repositories and presents information in a clean 2x2 grid layout:

### UI Layout

```
┌─────────────────────┬─────────────────────┐
│     Tech Stack      │  Features &         │
│   [Badge] [Badge]   │  Highlights         │
├─────────────────────┼─────────────────────┤
│     Strengths       │   Considerations    │
│  (green theme)      │   (amber theme)     │
└─────────────────────┴─────────────────────┘
┌─────────────────────────────────────────────┐
│ 📝 Summary: AI-generated or README excerpt  │
└─────────────────────────────────────────────┘
```

### Features

| Section | Description |
|---------|-------------|
| **Tech Stack** | Detected languages, frameworks, libraries, and tools with color-coded badges |
| **Features & Highlights** | Merged list of README features + detected highlights (AI, payments, real-time) |
| **Strengths** | What makes the project well-designed (deployment, architecture, monitoring) |
| **Considerations** | Areas to note or potential improvements |
| **Summary** | AI-generated summary (when OpenAI connected) or cleaned README excerpt |

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

### Automatic Detection

**Consideration Detection** - Automatically detects potential gaps:
- No authentication detected
- No database found
- No deployment configuration

**Summary Generation** - Clean text extraction:
- Strips HTML tags (`<p>`, `<img>`, etc.)
- Strips markdown images and links
- AI-powered summary when OpenAI is connected

## Post Generation System

### Value-First Framework

The AI prompt generator uses a **Value Framework** to drive engagement:

| Principle | Bad Example | Good Example |
|-----------|-------------|--------------|
| **Frustration-First Hook** | "I built a tool that does X" | "Tired of spending 2 hours configuring webpack?" |
| **3-Step Value Rule** | "Features real-time sync" | "Runs locally → Process sensitive data → Zero security risk" |
| **Active Voice** | "It has...", "It provides..." | "You can now...", "Say goodbye to..." |
| **Outcome Over Feature** | "Features real-time sync" | "Never lose work to a browser crash again" |

### Post Styles

Each style includes a **PRE-WRITING CHECKLIST** to guide the AI:

| Style | Hook Type | Key Question |
|-------|-----------|--------------|
| **Problem-Solution** | Frustration statement | "What specific frustration does this solve?" |
| **Tips & Learnings** | Counterintuitive insight | "What SURPRISED you while building this?" |
| **Technical Showcase** | Surprising metric or contrarian choice | "Why didn't you use [popular thing]?" |

### Audience Inference

The system automatically infers target audience from tech stack:

| Tech Stack | Inferred Audience |
|------------|-------------------|
| React, Vue, Angular, Next.js | Frontend developers |
| FastAPI, Django, Express, Flask | Backend developers |
| Docker, Kubernetes, Terraform | DevOps engineers |
| OpenAI, LangChain, Claude | AI/ML engineers |
| CLI tools, terminal keywords | Terminal workflow developers |

### Prompt Structure

The user prompt includes a **"SO WHAT?" Framework**:

```
Think about:
- What tedious task does this eliminate?
- What risky process does this make safe?
- What expensive thing does this make free?
- What complex thing does this make simple?
```

Features are presented with value prompts:
```
- Feature Name: Description
  → Think: What problem does this solve? What can the user now do?
```

## AI Image Generation

### Model
Uses **Gemini 3 Pro Image** (`gemini-3-pro-image-preview`) - also known as "Nano Banana Pro" - for high-quality LinkedIn post images.

### Supported Dimensions
| Format | Dimensions | Aspect Ratio | Image Size | Use Case |
|--------|------------|--------------|------------|----------|
| Link Post (default) | 1200x627 | 16:9 | 2K | Standard link preview |
| Square | 1080x1080 | 1:1 | 1K | Engagement posts |
| Large Square | 1200x1200 | 1:1 | 2K | Detailed visuals |

*Image Size parameter optimizes output quality per Gemini API best practices.*

### Image Styles
12 professionally designed styles (optimized for clean, artistic visuals):

| Style | Description | Mood |
|-------|-------------|------|
| **Infographic** | Bold typography as hero element | Clear, impactful, professional |
| **Minimalist** | Generous whitespace, one focal element | Elegant, sophisticated, premium |
| **Conceptual** | Dreamlike atmosphere, soft focus | Thought-provoking, inspiring |
| **Abstract** | Organic flowing shapes, color blending | Innovative, artistic, expressive |
| **Photorealistic** | Cinematic lighting, shallow depth of field | Authentic, premium, editorial |
| **Illustrated** | Flat illustration, smooth curves | Friendly, approachable, engaging |
| **Diagram** | Clean layout, visual hierarchy, bold text | Organized, clear, educational |
| **Gradient** | Gradient meshes, glass effects | Modern, dynamic, vibrant |
| **Flat Design** | Solid color blocks, simple shapes | Modern, clean, bold |
| **Isometric** | Stylized 3D, clean lines | Modern, dimensional, polished |
| **Tech Themed** | Neon glows, dark moody atmosphere | Innovative, cutting-edge, bold |
| **Professional** | Refined gradients, sophisticated typography | Trustworthy, established, premium |

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

The prompt builder generates clean, artistic visuals with explicit negative prompts to avoid technical diagrams:

```
Create a stunning LinkedIn [dimension] image.

VISUAL STYLE: [style description]. The mood is [mood].

COMPOSITION: [layout] layout with [background]. Add [foreground] for visual
interest. Use cinematic lighting with soft shadows and subtle depth.

TEXT OVERLAY: Display "[headline]" as the main headline in large, bold,
modern sans-serif typography. Below it, show "[subtitle]" in smaller,
lighter text. Ensure text is crisp and highly readable with strong contrast.

COLOR: Use professional colors that complement the content with rich,
harmonious tones.

CONTEXT: This accompanies a LinkedIn post about: [context summary]

CRITICAL - DO NOT INCLUDE:
- No diagrams, flowcharts, or charts
- No neural networks, nodes, or connection lines
- No code, terminals, or IDE screenshots
- No icons, logos, or clip art
- No busy infographics or data visualizations
- No stock photo watermarks

Create an artistic, premium quality image that looks like professional
marketing material, not a technical diagram.
```

**Key prompt optimizations:**
- Clean gradient backgrounds instead of technical elements
- Explicit negative prompts to avoid diagrams/charts
- Focus on typography and artistic composition
- Cinematic lighting and soft visual effects

## License

MIT
