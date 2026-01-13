# Product Requirements Document: OpenAI API Integration for LinkedIn Post Generation

**Version:** 2.3
**Project:** OpenAI API Integration
**Branch:** `ralph/openai-linkedin-post-generation`
**Created:** 2026-01-13
**Status:** Draft

---

## Overview & Goals

### Executive Summary

This feature extends the LinkedIn Content Automation system to support OpenAI as an alternative AI provider for generating LinkedIn posts based on GitHub repository analysis. Currently, users can only use Anthropic's Claude API; this enhancement provides choice and flexibility by enabling OpenAI's GPT models.

### Goals

1. **Provider Choice**: Allow users to use their existing OpenAI API keys instead of or alongside Claude
2. **Feature Parity**: Ensure OpenAI integration matches all existing Claude functionality (connect, disconnect, status, generate)
3. **Seamless UX**: Provide a unified, intuitive interface for managing multiple AI providers
4. **Security**: Maintain the same encryption and session-based security standards as Claude integration

### Success Metrics

- Users can successfully connect OpenAI API keys and generate posts
- No regression in existing Claude functionality
- API key security maintained (encryption, masking, session isolation)

---

## User Personas

### Persona 1: The Pragmatic Developer (Sarah Chen)
- **Role:** Full-Stack Developer at a mid-size SaaS company
- **Technical Level:** High - comfortable with APIs, has OpenAI key from ChatGPT experiments
- **Pain Point:** Already pays for ChatGPT Plus, doesn't want another AI subscription
- **Goal:** Use existing OpenAI credits for LinkedIn post generation

### Persona 2: The DevRel Professional (Marcus Johnson)
- **Role:** Developer Advocate at a tech company
- **Technical Level:** Medium-High - uses APIs but values simplicity
- **Pain Point:** Wants flexibility to use whichever AI produces better output
- **Goal:** Compare outputs from different AI providers for content quality

### Persona 3: The Enterprise Developer (Priya Sharma)
- **Role:** Senior Engineer at Fortune 500 company
- **Technical Level:** High - enterprise security-conscious
- **Pain Point:** Company has OpenAI enterprise agreement; Claude isn't approved
- **Goal:** Use company-approved AI vendor for content generation

### Persona 4: The AI Curious Newcomer (Alex Rivera)
- **Role:** Junior Developer, recent bootcamp graduate
- **Technical Level:** Medium - familiar with OpenAI from tutorials
- **Pain Point:** Already has OpenAI key from following tutorials
- **Goal:** Leverage familiar AI provider for building online presence

---

## Functional Requirements

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| FR-001 | OpenAI API Key Input | Users can enter their OpenAI API key through a secure form | Must |
| FR-002 | OpenAI Key Validation | System validates the API key by making a lightweight API call | Must |
| FR-003 | OpenAI Key Storage | API keys are encrypted with AES-256-GCM and stored in session | Must |
| FR-004 | OpenAI Connection Status | Display connection status with masked key (last 4 chars) | Must |
| FR-005 | OpenAI Disconnect | Users can remove their stored OpenAI API key | Must |
| FR-006 | OpenAI Post Generation | Generate LinkedIn posts using OpenAI GPT models | Must |
| FR-007 | Provider Selection | Users can choose between Claude and OpenAI when generating | Must |
| FR-008 | Error Handling | Handle OpenAI-specific errors (rate limits, quota, invalid key) | Must |
| FR-009 | Model Selection | Users can select GPT model (gpt-4o default, gpt-4, gpt-3.5-turbo) | Should |
| FR-010 | Remember Provider | System remembers last used provider preference | Should |

---

## Non-Functional Requirements

| ID | Title | Description | Priority |
|----|-------|-------------|----------|
| NFR-001 | Key Encryption | OpenAI keys encrypted with AES-256-GCM matching Claude pattern | Must |
| NFR-002 | Session Isolation | Keys isolated per session via X-Session-ID header | Must |
| NFR-003 | No Key Logging | API keys never appear in logs (filtered by `sk-` pattern) | Must |
| NFR-004 | Input Validation | All user inputs validated with Zod/Pydantic schemas | Must |
| NFR-005 | Response Time | Key validation completes within 5 seconds | Should |
| NFR-006 | Generation Time | Post generation completes within 60 seconds | Should |
| NFR-007 | TypeScript Strict | All TypeScript code passes strict mode | Must |
| NFR-008 | Test Coverage | New code has unit tests with Jest | Should |

---

## User Stories Summary

| ID | Title | Priority | Complexity | Est. Minutes |
|----|-------|----------|------------|--------------|
| US-001 | Create OpenAI Pydantic Schemas | 1 | 2 | 20 |
| US-002 | Implement OpenAI Client Service | 1 | 3 | 30 |
| US-003 | Create OpenAI Auth API Routes | 2 | 3 | 30 |
| US-004 | Extend Generation Route for OpenAI | 3 | 3 | 25 |
| US-005 | Add OpenAI State to Zustand Store | 4 | 2 | 20 |
| US-006 | Add OpenAI API Functions | 4 | 2 | 20 |
| US-007 | Create OpenAI Auth Form Component | 5 | 3 | 30 |
| US-008 | Create OpenAI Connection Status Component | 6 | 2 | 25 |
| US-009 | Create Provider Selector Component | 7 | 2 | 25 |
| US-010 | Integrate OpenAI Components into App | 8 | 3 | 30 |
| US-011 | Update AI Post Generator for Provider Selection | 9 | 3 | 30 |

---

## Scope

### In Scope

- OpenAI API key input, validation, storage, and disconnection
- OpenAI-powered LinkedIn post generation (same 3 styles as Claude)
- Provider selection UI when both providers connected
- Model selection (gpt-4o, gpt-4, gpt-3.5-turbo)
- Error handling for OpenAI-specific errors
- Masked key display for security
- Session-based key isolation

### Out of Scope

- Azure OpenAI support (different authentication model)
- OpenAI organization ID management
- Fine-tuned model support
- OpenAI Assistant API integration
- Persistent API usage history
- OpenAI image generation
- Cost estimation per generation
- Automatic provider fallback

---

## Open Questions

| # | Question | Recommended Answer |
|---|----------|--------------------|
| Q1 | Should both providers be connectable simultaneously? | Yes - provides flexibility |
| Q2 | Default model for OpenAI? | gpt-4o - best cost/quality balance |
| Q3 | Same prompts for OpenAI as Claude? | Start same, tune if needed |
| Q4 | Which provider is default when both connected? | Last used provider |
| Q5 | How to handle if user has neither provider connected? | Show connection prompts for both |

---

## Security Analysis Summary

### Data Classification
- **OpenAI API Key**: Secret credential, AES-256-GCM encrypted, session-scoped

### Key Threats & Mitigations
- **Key Exposure**: Masked display (last 4 chars), no logging, POST body only
- **Session Hijacking**: Secure session ID generation, HTTPS enforcement
- **Injection**: Input validation with Zod/Pydantic schemas

### OWASP Compliance
- A01 Broken Access Control: Session-based authorization
- A02 Cryptographic Failures: AES-256-GCM encryption
- A03 Injection: Input validation on all endpoints
- A07 Auth Failures: API key validation before storage

---

## Technical Architecture

### Backend Files (New)
- `backend/src/models/openai_schemas.py` - Request/response schemas
- `backend/src/services/openai_client.py` - OpenAI API client wrapper
- `backend/src/api/openai_routes.py` - Auth endpoints

### Backend Files (Modified)
- `backend/src/api/generate_routes.py` - Add provider parameter
- `backend/src/api/main.py` - Register new router

### Frontend Files (New)
- `frontend/src/components/openai-auth/OpenAIAuthForm.tsx`
- `frontend/src/components/openai-auth/OpenAIConnectionStatus.tsx`
- `frontend/src/components/provider/ProviderSelector.tsx`

### Frontend Files (Modified)
- `frontend/src/store/appStore.ts` - Add OpenAI state
- `frontend/src/lib/api.ts` - Add OpenAI API functions
- `frontend/src/App.tsx` - Integrate OpenAI components
- `frontend/src/components/posts/AIPostGenerator.tsx` - Provider selection
