import { create } from "zustand"
import type { AnalysisResult, GeneratedPrompt } from "@/lib/api"

type PostStyle = "problem-solution" | "tips-learnings" | "technical-showcase"

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
}

const initialClaudeAuthState: ClaudeAuthState = {
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
}))
