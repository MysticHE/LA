import { create } from "zustand"
import type { AnalysisResult, GeneratedPrompt } from "@/lib/api"

type PostStyle = "problem-solution" | "tips-learnings" | "technical-showcase"
type AIProvider = "claude" | "openai"

// Claude Auth Slice
interface ClaudeAuthState {
  isConnected: boolean
  maskedKey: string | null
  isLoading: boolean
  error: string | null
}

interface ClaudeAuthActions {
  setClaudeConnected: (connected: boolean, maskedKey?: string | null) => void
  setClaudeLoading: (loading: boolean) => void
  setClaudeError: (error: string | null) => void
  disconnectClaude: () => void
}

// OpenAI Auth Slice
interface OpenAIAuthState {
  isConnected: boolean
  maskedKey: string | null
  isLoading: boolean
  error: string | null
}

interface OpenAIAuthActions {
  setOpenAIConnected: (connected: boolean, maskedKey?: string | null) => void
  setOpenAILoading: (loading: boolean) => void
  setOpenAIError: (error: string | null) => void
  disconnectOpenAI: () => void
}

// Main App State
interface AppState {
  repoUrl: string
  analysis: AnalysisResult | null
  selectedStyle: PostStyle
  generatedPrompts: Record<PostStyle, GeneratedPrompt | null>
  isAnalyzing: boolean
  isGenerating: boolean
  error: string | null

  // Claude Auth
  claudeAuth: ClaudeAuthState

  // OpenAI Auth
  openaiAuth: OpenAIAuthState

  // Provider Selection
  selectedProvider: AIProvider | null

  setRepoUrl: (url: string) => void
  setAnalysis: (result: AnalysisResult | null) => void
  setSelectedStyle: (style: PostStyle) => void
  setGeneratedPrompt: (style: PostStyle, prompt: GeneratedPrompt) => void
  setIsAnalyzing: (value: boolean) => void
  setIsGenerating: (value: boolean) => void
  setError: (error: string | null) => void
  reset: () => void

  // Claude Auth Actions
  setClaudeConnected: ClaudeAuthActions["setClaudeConnected"]
  setClaudeLoading: ClaudeAuthActions["setClaudeLoading"]
  setClaudeError: ClaudeAuthActions["setClaudeError"]
  disconnectClaude: ClaudeAuthActions["disconnectClaude"]

  // OpenAI Auth Actions
  setOpenAIConnected: OpenAIAuthActions["setOpenAIConnected"]
  setOpenAILoading: OpenAIAuthActions["setOpenAILoading"]
  setOpenAIError: OpenAIAuthActions["setOpenAIError"]
  disconnectOpenAI: OpenAIAuthActions["disconnectOpenAI"]

  // Provider Selection Action
  setSelectedProvider: (provider: AIProvider | null) => void
}

const initialClaudeAuthState: ClaudeAuthState = {
  isConnected: false,
  maskedKey: null,
  isLoading: false,
  error: null,
}

const initialOpenAIAuthState: OpenAIAuthState = {
  isConnected: false,
  maskedKey: null,
  isLoading: false,
  error: null,
}

const initialState = {
  repoUrl: "",
  analysis: null,
  selectedStyle: "problem-solution" as PostStyle,
  generatedPrompts: {
    "problem-solution": null,
    "tips-learnings": null,
    "technical-showcase": null,
  },
  isAnalyzing: false,
  isGenerating: false,
  error: null,
  claudeAuth: initialClaudeAuthState,
  openaiAuth: initialOpenAIAuthState,
  selectedProvider: null as AIProvider | null,
}

export const useAppStore = create<AppState>((set) => ({
  ...initialState,

  setRepoUrl: (url) => set({ repoUrl: url }),
  setAnalysis: (result) => set({ analysis: result }),
  setSelectedStyle: (style) => set({ selectedStyle: style }),
  setGeneratedPrompt: (style, prompt) =>
    set((state) => ({
      generatedPrompts: {
        ...state.generatedPrompts,
        [style]: prompt,
      },
    })),
  setIsAnalyzing: (value) => set({ isAnalyzing: value }),
  setIsGenerating: (value) => set({ isGenerating: value }),
  setError: (error) => set({ error }),
  reset: () => set(initialState),

  // Claude Auth Actions
  setClaudeConnected: (connected, maskedKey = null) =>
    set((state) => ({
      claudeAuth: {
        ...state.claudeAuth,
        isConnected: connected,
        maskedKey: connected ? maskedKey : null,
        error: null,
      },
    })),
  setClaudeLoading: (loading) =>
    set((state) => ({
      claudeAuth: {
        ...state.claudeAuth,
        isLoading: loading,
      },
    })),
  setClaudeError: (error) =>
    set((state) => ({
      claudeAuth: {
        ...state.claudeAuth,
        error,
        isLoading: false,
      },
    })),
  disconnectClaude: () =>
    set({
      claudeAuth: {
        ...initialClaudeAuthState,
      },
    }),

  // OpenAI Auth Actions
  setOpenAIConnected: (connected, maskedKey = null) =>
    set((state) => ({
      openaiAuth: {
        ...state.openaiAuth,
        isConnected: connected,
        maskedKey: connected ? maskedKey : null,
        error: null,
      },
    })),
  setOpenAILoading: (loading) =>
    set((state) => ({
      openaiAuth: {
        ...state.openaiAuth,
        isLoading: loading,
      },
    })),
  setOpenAIError: (error) =>
    set((state) => ({
      openaiAuth: {
        ...state.openaiAuth,
        error,
        isLoading: false,
      },
    })),
  disconnectOpenAI: () =>
    set({
      openaiAuth: {
        ...initialOpenAIAuthState,
      },
    }),

  // Provider Selection Action
  setSelectedProvider: (provider) => set({ selectedProvider: provider }),
}))
