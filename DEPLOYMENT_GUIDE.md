# Deployment Guide: Render + LinkedIn Setup

## Table of Contents
1. [Render Deployment](#render-deployment)
   - [Backend (Python/FastAPI)](#1-deploy-backend-pythonfastapi)
   - [Frontend (React/Vite)](#2-deploy-frontend-reactvite)
   - [Environment Variables](#3-environment-variables)
2. [LinkedIn Integration](#linkedin-integration)
   - [Current Workflow (No API)](#option-a-current-workflow-no-api-needed)
   - [Future: LinkedIn API Setup](#option-b-future-linkedin-api-for-auto-posting)
3. [GitHub Token Setup](#github-token-setup)

---

## Render Deployment

### Prerequisites
- Render account (https://render.com - free tier available)
- GitHub repository connected to Render

### 1. Deploy Backend (Python/FastAPI)

#### Step 1: Create Backend Service
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository: `MysticHE/LA`
4. Configure the service:

| Setting | Value |
|---------|-------|
| **Name** | `linkedin-content-api` |
| **Region** | Singapore (or closest to you) |
| **Branch** | `main` |
| **Root Directory** | `backend` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn src.api.main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | Free |

#### Step 2: Add Environment Variables
In Render dashboard → Your service → **Environment** tab:

| Key | Value | Description |
|-----|-------|-------------|
| `GITHUB_TOKEN` | `ghp_xxxx...` | Your GitHub Personal Access Token |
| `PYTHON_VERSION` | `3.11.0` | Python version |

#### Step 3: Create `render.yaml` (Optional - for Infrastructure as Code)

Create this file in your repo root for automatic configuration:

```yaml
# render.yaml
services:
  # Backend API
  - type: web
    name: linkedin-content-api
    runtime: python
    region: singapore
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GITHUB_TOKEN
        sync: false  # Set manually in dashboard
      - key: PYTHON_VERSION
        value: 3.11.0
    autoDeploy: true

  # Frontend Static Site
  - type: web
    name: linkedin-content-frontend
    runtime: static
    region: singapore
    rootDir: frontend
    buildCommand: npm install && npm run build
    staticPublishPath: dist
    headers:
      - path: /*
        name: Cache-Control
        value: public, max-age=0, must-revalidate
    routes:
      - type: rewrite
        source: /*
        destination: /index.html
    autoDeploy: true
```

---

### 2. Deploy Frontend (React/Vite)

#### Step 1: Create Static Site
1. In Render Dashboard, click **"New +"** → **"Static Site"**
2. Connect the same GitHub repository
3. Configure:

| Setting | Value |
|---------|-------|
| **Name** | `linkedin-content-frontend` |
| **Branch** | `main` |
| **Root Directory** | `frontend` |
| **Build Command** | `npm install && npm run build` |
| **Publish Directory** | `dist` |

#### Step 2: Update Frontend API URL

Before deploying, update the API base URL in your frontend to point to the Render backend.

**File: `frontend/src/lib/api.ts`**

Change:
```typescript
const API_BASE_URL = "http://localhost:8000/api"
```

To:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api"
```

#### Step 3: Add Environment Variable in Render
In Render → Frontend service → **Environment** tab:

| Key | Value |
|-----|-------|
| `VITE_API_URL` | `https://linkedin-content-api.onrender.com/api` |

> Replace with your actual backend URL from Render

#### Step 4: Add Redirect Rules
In Render → Frontend service → **Redirects/Rewrites** tab:

| Source | Destination | Type |
|--------|-------------|------|
| `/*` | `/index.html` | Rewrite |

This enables client-side routing.

---

### 3. Environment Variables

#### Backend Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GITHUB_TOKEN` | Optional | For analyzing private repos |
| `PYTHON_VERSION` | Optional | Specify Python version |

#### Frontend Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | Yes | Backend API URL |

---

### 4. Auto-Deploy Setup

Render automatically deploys when you push to the connected branch.

**To enable/disable:**
1. Go to your service in Render
2. Click **Settings** tab
3. Scroll to **Build & Deploy**
4. Toggle **"Auto-Deploy"** on/off

**Branch Deploy:**
- Commits to `main` → triggers production deploy
- Pull requests can trigger preview deploys (Render Pro feature)

---

### 5. Update CORS in Backend

Update `backend/src/api/main.py` to allow your Render frontend domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://linkedin-content-frontend.onrender.com",  # Add your Render frontend URL
        "https://your-custom-domain.com",  # If you add a custom domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## LinkedIn Integration

### Option A: Current Workflow (No API Needed)

Your current system generates **prompts** that you paste into Claude Code. This workflow doesn't require LinkedIn API access:

```
GitHub Repo → Analyze → Generate Prompt → Copy to Claude Code → Get Post → Manually Post to LinkedIn
```

**Advantages:**
- No LinkedIn API approval needed
- No rate limits
- Full control over content before posting
- Works immediately

---

### Option B: Future LinkedIn API (For Auto-Posting)

If you want to add **automatic posting** to LinkedIn in the future:

#### Step 1: Create LinkedIn App

1. Go to [LinkedIn Developers](https://www.linkedin.com/developers/)
2. Click **"Create App"**
3. Fill in details:

| Field | Value |
|-------|-------|
| App name | `LinkedIn Content Generator` |
| LinkedIn Page | Your company page (required) |
| App logo | Upload a logo |
| Legal agreement | Check the box |

4. Click **"Create app"**

#### Step 2: Request API Products

In your app settings → **Products** tab:

| Product | Purpose | Approval |
|---------|---------|----------|
| **Share on LinkedIn** | Post content | Auto-approved |
| **Sign In with LinkedIn using OpenID Connect** | Authentication | Auto-approved |
| **Marketing Developer Platform** | Advanced posting | Requires application |

> **Note:** For personal posting, "Share on LinkedIn" is sufficient.

#### Step 3: Get Credentials

In **Auth** tab, note down:
- **Client ID**
- **Client Secret**

Add **Redirect URLs**:
```
https://linkedin-content-frontend.onrender.com/callback
http://localhost:5173/callback
```

#### Step 4: OAuth 2.0 Scopes

Request these scopes:

| Scope | Purpose |
|-------|---------|
| `openid` | OpenID Connect |
| `profile` | Basic profile info |
| `w_member_social` | Post on behalf of user |

#### Step 5: Implement OAuth Flow

**Backend endpoint for auth:**

```python
# backend/src/api/linkedin.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
import httpx
import os

router = APIRouter(prefix="/linkedin")

CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
CLIENT_SECRET = os.getenv("LINKEDIN_CLIENT_SECRET")
REDIRECT_URI = os.getenv("LINKEDIN_REDIRECT_URI")

@router.get("/auth")
async def linkedin_auth():
    """Redirect to LinkedIn OAuth"""
    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=openid%20profile%20w_member_social"
    )
    return RedirectResponse(auth_url)

@router.get("/callback")
async def linkedin_callback(code: str):
    """Handle OAuth callback and get access token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
            },
        )
        tokens = response.json()
        # Store tokens securely (database, encrypted storage)
        return {"access_token": tokens.get("access_token")}

@router.post("/post")
async def create_post(content: str, access_token: str):
    """Create a LinkedIn post"""
    async with httpx.AsyncClient() as client:
        # Get user ID first
        me_response = await client.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_id = me_response.json()["sub"]

        # Create post
        post_response = await client.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            },
            json={
                "author": f"urn:li:person:{user_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": content},
                        "shareMediaCategory": "NONE",
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
            },
        )
        return post_response.json()
```

#### Step 6: Environment Variables for LinkedIn

Add to Render backend:

| Key | Value |
|-----|-------|
| `LINKEDIN_CLIENT_ID` | Your Client ID |
| `LINKEDIN_CLIENT_SECRET` | Your Client Secret |
| `LINKEDIN_REDIRECT_URI` | `https://your-backend.onrender.com/api/linkedin/callback` |

---

## GitHub Token Setup

For analyzing private repositories, you need a GitHub Personal Access Token.

### Create GitHub Token

1. Go to [GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)](https://github.com/settings/tokens)
2. Click **"Generate new token (classic)"**
3. Configure:

| Setting | Value |
|---------|-------|
| Note | `LinkedIn Content Generator` |
| Expiration | 90 days (or custom) |
| Scopes | `repo` (Full control of private repositories) |

4. Click **"Generate token"**
5. **Copy the token immediately** (you won't see it again)

### Add to Render

1. Go to Render Dashboard → Backend service
2. Click **Environment** tab
3. Add:
   - Key: `GITHUB_TOKEN`
   - Value: `ghp_your_token_here`
4. Click **Save Changes**

---

## Deployment Checklist

### Before Deploying

- [ ] Update `frontend/src/lib/api.ts` to use environment variable
- [ ] Update `backend/src/api/main.py` CORS settings
- [ ] Create GitHub Personal Access Token
- [ ] Commit and push changes to GitHub

### Render Setup

- [ ] Create Backend Web Service
- [ ] Add backend environment variables (`GITHUB_TOKEN`)
- [ ] Create Frontend Static Site
- [ ] Add frontend environment variable (`VITE_API_URL`)
- [ ] Add redirect rules for frontend
- [ ] Verify auto-deploy is enabled

### After Deployment

- [ ] Test backend API: `https://your-backend.onrender.com/docs`
- [ ] Test frontend: `https://your-frontend.onrender.com`
- [ ] Test full workflow: Analyze repo → Generate prompt → Copy

---

## Troubleshooting

### Backend won't start
- Check logs in Render dashboard
- Verify `requirements.txt` has all dependencies
- Ensure start command uses `$PORT` variable

### Frontend can't reach backend
- Check CORS settings include frontend domain
- Verify `VITE_API_URL` is set correctly
- Check browser console for errors

### GitHub API rate limit
- Add `GITHUB_TOKEN` environment variable
- Authenticated requests get 5,000/hour vs 60/hour

### Build fails
- Check build logs in Render
- Verify root directory is correct
- Ensure all dependencies are in package.json/requirements.txt

---

## URLs After Deployment

| Service | URL Pattern |
|---------|-------------|
| Backend API | `https://linkedin-content-api.onrender.com` |
| API Docs | `https://linkedin-content-api.onrender.com/docs` |
| Frontend | `https://linkedin-content-frontend.onrender.com` |

> Note: Free tier services spin down after 15 minutes of inactivity. First request after spin-down may take 30-60 seconds.
