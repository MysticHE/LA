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
}
