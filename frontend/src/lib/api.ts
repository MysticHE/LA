import { getSessionId } from './session'

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api"

// Error type for API errors
export class ApiError extends Error {
  readonly code: string
  readonly retryable: boolean
  readonly retryAfter?: number

  constructor(
    message: string,
    code: string,
    retryable = false,
    retryAfter?: number
  ) {
    super(message)
    this.name = "ApiError"
    this.code = code
    this.retryable = retryable
    this.retryAfter = retryAfter
  }
}

// User-friendly error messages map
const ERROR_MESSAGES: Record<string, string> = {
  // Network errors
  NETWORK_ERROR: "Unable to connect to the server. Please check your internet connection.",
  TIMEOUT_ERROR: "The request took too long. Please try again.",
  // Claude API errors
  INVALID_API_KEY: "The API key is invalid. Please check your key and try again.",
  RATE_LIMITED: "You've made too many requests. Please wait before trying again.",
  PERMISSION_DENIED: "Your API key doesn't have permission for this operation.",
  SERVICE_UNAVAILABLE: "Claude service is temporarily unavailable. Please try again later.",
  // Generic errors
  UNKNOWN_ERROR: "Something went wrong. Please try again.",
}

/**
 * Maps technical error messages to user-friendly ones
 */
export function getUserFriendlyError(error: string, code = "UNKNOWN_ERROR"): string {
  if (ERROR_MESSAGES[code]) {
    return ERROR_MESSAGES[code]
  }

  // Map common error patterns to user-friendly messages
  const errorLower = error.toLowerCase()
  if (errorLower.includes("network") || errorLower.includes("fetch") || errorLower.includes("failed to fetch")) {
    return ERROR_MESSAGES.NETWORK_ERROR
  }
  if (errorLower.includes("timeout") || errorLower.includes("aborted")) {
    return ERROR_MESSAGES.TIMEOUT_ERROR
  }
  if (errorLower.includes("invalid") && errorLower.includes("key")) {
    return ERROR_MESSAGES.INVALID_API_KEY
  }
  if (errorLower.includes("rate") || errorLower.includes("429") || errorLower.includes("too many")) {
    return ERROR_MESSAGES.RATE_LIMITED
  }
  if (errorLower.includes("permission") || errorLower.includes("403") || errorLower.includes("forbidden")) {
    return ERROR_MESSAGES.PERMISSION_DENIED
  }
  if (errorLower.includes("unavailable") || errorLower.includes("503") || errorLower.includes("service")) {
    return ERROR_MESSAGES.SERVICE_UNAVAILABLE
  }

  // Return the original message if no mapping found (but sanitized)
  return error || ERROR_MESSAGES.UNKNOWN_ERROR
}

/**
 * Wraps fetch with timeout handling
 */
async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeout = 30000
): Promise<Response> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    })
    return response
  } catch (error) {
    if (error instanceof Error) {
      if (error.name === "AbortError") {
        throw new ApiError(
          ERROR_MESSAGES.TIMEOUT_ERROR,
          "TIMEOUT_ERROR",
          true
        )
      }
      throw new ApiError(
        getUserFriendlyError(error.message),
        "NETWORK_ERROR",
        true
      )
    }
    throw new ApiError(ERROR_MESSAGES.UNKNOWN_ERROR, "UNKNOWN_ERROR", true)
  } finally {
    clearTimeout(timeoutId)
  }
}

export interface TechStackItem {
  name: string
  category: string
}

export interface Feature {
  name: string
  description: string
}

export type InsightType = "strength" | "consideration" | "highlight"

export interface ProjectInsight {
  type: InsightType
  title: string
  description: string
  icon: string
}

export interface AnalysisResult {
  repo_name: string
  description: string | null
  stars: number
  forks: number
  language: string | null
  tech_stack: TechStackItem[]
  features: Feature[]  // Merged features + highlights
  readme_summary: string | null  // Fallback text summary
  ai_summary: string | null  // AI-generated summary
  file_structure: string[]
  insights: ProjectInsight[]  // Only strengths + considerations
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

// OpenAI Auth Types
export interface OpenAIAuthResponse {
  connected: boolean
  masked_key: string | null
  error?: string
}

export interface OpenAIStatusResponse {
  connected: boolean
  masked_key: string | null
}

// Gemini Auth Types
export interface GeminiAuthResponse {
  connected: boolean
  masked_key: string | null
  error?: string
}

export interface GeminiStatusResponse {
  connected: boolean
  masked_key: string | null
}

// AI Provider Type
export type AIProvider = 'claude' | 'openai'

// Repository Ownership Type
export type RepositoryOwnership = 'own' | 'discovered'

// AI Generation Types
export interface AIGenerateRequest {
  analysis: AnalysisResult
  style: string
}

export interface AIGenerateResponse {
  success: boolean
  content: string | null
  style: string | null
  error?: string
  retry_after?: number
}

// Image Generation Types
export type ImageModelId =
  | "gemini-3-pro-image-preview"
  | "imagen-4.0-ultra-generate-001"
  | "imagen-4.0-generate-001"
  | "imagen-4.0-fast-generate-001"
  | "gemini-2.5-flash-image"

export interface ImageGenerationRequest {
  postContent: string
  style?: string
  dimensions: string
  customPrompt?: string
  model?: ImageModelId
}

export interface ImageGenerationResponse {
  success: boolean
  image_base64?: string
  content_type?: string
  recommended_style?: string
  dimensions?: string
  prompt_used?: string
  error?: string
  retry_after?: number
}

export interface StyleRecommendationResponse {
  styles: string[]
  content_type: string | null
  tech_influenced: boolean
}

export const api = {
  async analyzeRepo(url: string, token?: string): Promise<ApiResponse<AnalysisResult>> {
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Session-ID": getSessionId(),
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
  async connectClaude(apiKey: string): Promise<ClaudeAuthResponse> {
    const response = await fetchWithTimeout(`${API_BASE_URL}/auth/claude/connect`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Session-ID": getSessionId(),
      },
      body: JSON.stringify({ api_key: apiKey }),
    })

    // Handle error responses with user-friendly messages
    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      const errorMessage = data.detail || data.error || `Request failed with status ${response.status}`
      return {
        connected: false,
        masked_key: null,
        error: getUserFriendlyError(errorMessage),
      }
    }

    return response.json()
  },

  async getClaudeStatus(): Promise<ClaudeStatusResponse> {
    const response = await fetchWithTimeout(`${API_BASE_URL}/auth/claude/status`, {
      headers: {
        "X-Session-ID": getSessionId(),
      },
    })
    return response.json()
  },

  async disconnectClaude(): Promise<ClaudeAuthResponse> {
    const response = await fetchWithTimeout(`${API_BASE_URL}/auth/claude/disconnect`, {
      method: "POST",
      headers: {
        "X-Session-ID": getSessionId(),
      },
    })

    // Handle error responses with user-friendly messages
    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      const errorMessage = data.detail || data.error || `Request failed with status ${response.status}`
      return {
        connected: true, // Keep connected on error
        masked_key: null,
        error: getUserFriendlyError(errorMessage),
      }
    }

    return response.json()
  },

  // OpenAI Auth API
  async connectOpenAI(apiKey: string): Promise<OpenAIAuthResponse> {
    const response = await fetchWithTimeout(`${API_BASE_URL}/auth/openai/connect`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Session-ID": getSessionId(),
      },
      body: JSON.stringify({ api_key: apiKey }),
    })

    // Handle error responses with user-friendly messages
    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      const errorMessage = data.detail || data.error || `Request failed with status ${response.status}`
      return {
        connected: false,
        masked_key: null,
        error: getUserFriendlyError(errorMessage),
      }
    }

    return response.json()
  },

  async getOpenAIStatus(): Promise<OpenAIStatusResponse> {
    const response = await fetchWithTimeout(`${API_BASE_URL}/auth/openai/status`, {
      headers: {
        "X-Session-ID": getSessionId(),
      },
    })
    return response.json()
  },

  async disconnectOpenAI(): Promise<OpenAIAuthResponse> {
    const response = await fetchWithTimeout(`${API_BASE_URL}/auth/openai/disconnect`, {
      method: "POST",
      headers: {
        "X-Session-ID": getSessionId(),
      },
    })

    // Handle error responses with user-friendly messages
    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      const errorMessage = data.detail || data.error || `Request failed with status ${response.status}`
      return {
        connected: true, // Keep connected on error
        masked_key: null,
        error: getUserFriendlyError(errorMessage),
      }
    }

    return response.json()
  },

  // Gemini Auth API
  async connectGemini(apiKey: string): Promise<GeminiAuthResponse> {
    const response = await fetchWithTimeout(`${API_BASE_URL}/auth/gemini/connect`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Session-ID": getSessionId(),
      },
      body: JSON.stringify({ api_key: apiKey }),
    })

    // Handle error responses with user-friendly messages
    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      const errorMessage = data.detail || data.error || `Request failed with status ${response.status}`
      return {
        connected: false,
        masked_key: null,
        error: getUserFriendlyError(errorMessage),
      }
    }

    return response.json()
  },

  async getGeminiStatus(): Promise<GeminiStatusResponse> {
    const response = await fetchWithTimeout(`${API_BASE_URL}/auth/gemini/status`, {
      headers: {
        "X-Session-ID": getSessionId(),
      },
    })
    return response.json()
  },

  async disconnectGemini(): Promise<GeminiAuthResponse> {
    const response = await fetchWithTimeout(`${API_BASE_URL}/auth/gemini/disconnect`, {
      method: "POST",
      headers: {
        "X-Session-ID": getSessionId(),
      },
    })

    // Handle error responses with user-friendly messages
    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      const errorMessage = data.detail || data.error || `Request failed with status ${response.status}`
      return {
        connected: true, // Keep connected on error
        masked_key: null,
        error: getUserFriendlyError(errorMessage),
      }
    }

    return response.json()
  },

  // AI Generation API
  async generateAIPost(
    analysis: AnalysisResult,
    style: string,
    provider: AIProvider = 'claude',
    model?: string,
    ownership: RepositoryOwnership = 'own'
  ): Promise<AIGenerateResponse> {
    const requestBody: Record<string, unknown> = { analysis, style, provider, ownership }
    if (model) {
      requestBody.model = model
    }

    const response = await fetchWithTimeout(
      `${API_BASE_URL}/generate/ai-post`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-ID": getSessionId(),
        },
        body: JSON.stringify(requestBody),
      },
      60000 // 60 second timeout for AI generation
    )

    // Handle rate limit with retry_after
    if (response.status === 429) {
      const retryAfter = response.headers.get("Retry-After")
      const data = await response.json().catch(() => ({}))
      return {
        success: false,
        content: null,
        style: style,
        error: getUserFriendlyError(data.detail || "Rate limit exceeded", "RATE_LIMITED"),
        retry_after: retryAfter ? parseInt(retryAfter, 10) : 60,
      }
    }

    // Handle unauthorized (not connected)
    if (response.status === 401) {
      const data = await response.json().catch(() => ({}))
      const providerName = provider === 'openai' ? 'OpenAI' : 'Claude'
      return {
        success: false,
        content: null,
        style: style,
        error: data.detail || `Not connected to ${providerName}. Please connect your API key.`,
      }
    }

    // Handle other error responses
    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      const errorMessage = data.detail || data.error || `Request failed with status ${response.status}`
      return {
        success: false,
        content: null,
        style: style,
        error: getUserFriendlyError(errorMessage),
      }
    }

    return response.json()
  },

  // Style Recommendation API
  async getStyleRecommendations(postContent: string): Promise<StyleRecommendationResponse> {
    if (!postContent.trim()) {
      return { styles: [], content_type: null, tech_influenced: false }
    }

    const response = await fetchWithTimeout(
      `${API_BASE_URL}/generate/image/recommend`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ content: postContent }),
      },
      10000 // 10 second timeout for recommendations
    )

    if (!response.ok) {
      return { styles: [], content_type: null, tech_influenced: false }
    }

    return response.json()
  },

  // Image Generation API
  async generateImage(request: ImageGenerationRequest): Promise<ImageGenerationResponse> {
    const requestBody: Record<string, unknown> = {
      post_content: request.postContent,
      dimensions: request.dimensions,
    }
    if (request.style) {
      requestBody.style = request.style
    }
    if (request.customPrompt) {
      requestBody.custom_prompt = request.customPrompt
    }
    if (request.model) {
      requestBody.model = request.model
    }

    const response = await fetchWithTimeout(
      `${API_BASE_URL}/generate/image`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Session-ID": getSessionId(),
        },
        body: JSON.stringify(requestBody),
      },
      120000 // 120 second timeout for image generation
    )

    // Handle rate limit with retry_after
    if (response.status === 429) {
      const retryAfter = response.headers.get("Retry-After")
      const data = await response.json().catch(() => ({}))
      return {
        success: false,
        error: getUserFriendlyError(data.detail || "Rate limit exceeded", "RATE_LIMITED"),
        retry_after: retryAfter ? parseInt(retryAfter, 10) : 60,
      }
    }

    // Handle unauthorized (not connected)
    if (response.status === 401) {
      const data = await response.json().catch(() => ({}))
      return {
        success: false,
        error: data.detail || "Not connected to Gemini. Please connect your API key.",
      }
    }

    // Handle other error responses
    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      const errorMessage = data.detail || data.error || `Request failed with status ${response.status}`
      return {
        success: false,
        error: getUserFriendlyError(errorMessage),
      }
    }

    return response.json()
  },
}
