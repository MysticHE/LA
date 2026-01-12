const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api"

export interface TechStackItem {
  name: string
  category: string
}

export interface Feature {
  name: string
  description: string
}

export interface AnalysisResult {
  repo_name: string
  description: string | null
  stars: number
  forks: number
  language: string | null
  tech_stack: TechStackItem[]
  features: Feature[]
  readme_summary: string | null
  file_structure: string[]
}

export interface GeneratedPrompt {
  style: string
  prompt: string
  instructions: string
}

export interface TemplateInfo {
  id: string
  name: string
  description: string
}

export interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
}

// Claude Auth Types
export interface ClaudeAuthResponse {
  connected: boolean
  masked_key: string | null
  error?: string
}

export interface ClaudeStatusResponse {
  connected: boolean
  masked_key: string | null
}

export const api = {
  async analyzeRepo(url: string, token?: string): Promise<ApiResponse<AnalysisResult>> {
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url, token }),
    })
    return response.json()
  },

  async generatePrompt(
    analysis: AnalysisResult,
    style: string
  ): Promise<ApiResponse<GeneratedPrompt>> {
    const response = await fetch(`${API_BASE_URL}/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ analysis, style }),
    })
    return response.json()
  },

  async getTemplates(): Promise<TemplateInfo[]> {
    const response = await fetch(`${API_BASE_URL}/templates`)
    return response.json()
  },

  // Claude Auth API
  async connectClaude(apiKey: string, sessionId = "default"): Promise<ClaudeAuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/claude/connect`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Session-ID": sessionId,
      },
      body: JSON.stringify({ api_key: apiKey }),
    })
    return response.json()
  },

  async getClaudeStatus(sessionId = "default"): Promise<ClaudeStatusResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/claude/status`, {
      headers: {
        "X-Session-ID": sessionId,
      },
    })
    return response.json()
  },

  async disconnectClaude(sessionId = "default"): Promise<ClaudeAuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/claude/disconnect`, {
      method: "POST",
      headers: {
        "X-Session-ID": sessionId,
      },
    })
    return response.json()
  },
}
