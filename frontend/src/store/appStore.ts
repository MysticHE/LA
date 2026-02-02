import { create } from "zustand"
import type { AnalysisResult, GeneratedPrompt, ContentAnalysisResult, RepurposeStyle, RepurposeFormat, ImageContext } from "@/lib/api"

type PostStyle = "problem-solution" | "tips-learnings" | "technical-showcase"
type AIProvider = "claude" | "openai"
type InputMode = "github" | "linkedin"

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

// Gemini Auth Slice
interface GeminiAuthState {
  isConnected: boolean
  maskedKey: string | null
  isLoading: boolean
  error: string | null
}

interface GeminiAuthActions {
  setGeminiConnected: (connected: boolean, maskedKey?: string | null) => void
  setGeminiLoading: (loading: boolean) => void
  setGeminiError: (error: string | null) => void
  disconnectGemini: () => void
}

// LinkedIn Repurpose State
interface LinkedInState {
  originalContent: string
  contentAnalysis: ContentAnalysisResult | null
  repurposedContent: string | null
  suggestedHashtags: string[]
  imageContext: ImageContext | null
  targetStyle: RepurposeStyle
  targetFormat: RepurposeFormat
  isAnalyzingLinkedIn: boolean
  isRepurposing: boolean
  linkedInError: string | null
}

interface LinkedInActions {
  setOriginalContent: (content: string) => void
  setContentAnalysis: (analysis: ContentAnalysisResult | null) => void
  setRepurposedContent: (content: string | null) => void
  setSuggestedHashtags: (hashtags: string[]) => void
  setImageContext: (context: ImageContext | null) => void
  setTargetStyle: (style: RepurposeStyle) => void
  setTargetFormat: (format: RepurposeFormat) => void
  setIsAnalyzingLinkedIn: (value: boolean) => void
  setIsRepurposing: (value: boolean) => void
  setLinkedInError: (error: string | null) => void
  resetLinkedIn: () => void
}

// Main App State
interface AppState {
  // Input mode
  inputMode: InputMode

  // GitHub state
  repoUrl: string
  analysis: AnalysisResult | null
  selectedStyle: PostStyle
  generatedPrompts: Record<PostStyle, GeneratedPrompt | null>
  isAnalyzing: boolean
  isGenerating: boolean
  error: string | null

  // LinkedIn state
  linkedin: LinkedInState

  // Claude Auth
  claudeAuth: ClaudeAuthState

  // OpenAI Auth
  openaiAuth: OpenAIAuthState

  // Gemini Auth
  geminiAuth: GeminiAuthState

  // Provider Selection
  selectedProvider: AIProvider | null

  // Input mode action
  setInputMode: (mode: InputMode) => void

  // GitHub actions
  setRepoUrl: (url: string) => void
  setAnalysis: (result: AnalysisResult | null) => void
  setSelectedStyle: (style: PostStyle) => void
  setGeneratedPrompt: (style: PostStyle, prompt: GeneratedPrompt) => void
  setIsAnalyzing: (value: boolean) => void
  setIsGenerating: (value: boolean) => void
  setError: (error: string | null) => void
  reset: () => void

  // LinkedIn actions
  setOriginalContent: LinkedInActions["setOriginalContent"]
  setContentAnalysis: LinkedInActions["setContentAnalysis"]
  setRepurposedContent: LinkedInActions["setRepurposedContent"]
  setSuggestedHashtags: LinkedInActions["setSuggestedHashtags"]
  setImageContext: LinkedInActions["setImageContext"]
  setTargetStyle: LinkedInActions["setTargetStyle"]
  setTargetFormat: LinkedInActions["setTargetFormat"]
  setIsAnalyzingLinkedIn: LinkedInActions["setIsAnalyzingLinkedIn"]
  setIsRepurposing: LinkedInActions["setIsRepurposing"]
  setLinkedInError: LinkedInActions["setLinkedInError"]
  resetLinkedIn: LinkedInActions["resetLinkedIn"]

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

  // Gemini Auth Actions
  setGeminiConnected: GeminiAuthActions["setGeminiConnected"]
  setGeminiLoading: GeminiAuthActions["setGeminiLoading"]
  setGeminiError: GeminiAuthActions["setGeminiError"]
  disconnectGemini: GeminiAuthActions["disconnectGemini"]

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

const initialGeminiAuthState: GeminiAuthState = {
  isConnected: false,
  maskedKey: null,
  isLoading: false,
  error: null,
}

const initialLinkedInState: LinkedInState = {
  originalContent: "",
  contentAnalysis: null,
  repurposedContent: null,
  suggestedHashtags: [],
  imageContext: null,
  targetStyle: "same",
  targetFormat: "expanded",
  isAnalyzingLinkedIn: false,
  isRepurposing: false,
  linkedInError: null,
}

const initialState = {
  inputMode: "github" as InputMode,
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
  linkedin: initialLinkedInState,
  claudeAuth: initialClaudeAuthState,
  openaiAuth: initialOpenAIAuthState,
  geminiAuth: initialGeminiAuthState,
  selectedProvider: null as AIProvider | null,
}

export const useAppStore = create<AppState>((set) => ({
  ...initialState,

  // Input mode
  setInputMode: (mode) => set({ inputMode: mode }),

  // GitHub actions
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

  // Gemini Auth Actions
  setGeminiConnected: (connected, maskedKey = null) =>
    set((state) => ({
      geminiAuth: {
        ...state.geminiAuth,
        isConnected: connected,
        maskedKey: connected ? maskedKey : null,
        error: null,
      },
    })),
  setGeminiLoading: (loading) =>
    set((state) => ({
      geminiAuth: {
        ...state.geminiAuth,
        isLoading: loading,
      },
    })),
  setGeminiError: (error) =>
    set((state) => ({
      geminiAuth: {
        ...state.geminiAuth,
        error,
        isLoading: false,
      },
    })),
  disconnectGemini: () =>
    set({
      geminiAuth: {
        ...initialGeminiAuthState,
      },
    }),

  // Provider Selection Action
  setSelectedProvider: (provider) => set({ selectedProvider: provider }),

  // LinkedIn Actions
  setOriginalContent: (content) =>
    set((state) => ({
      linkedin: { ...state.linkedin, originalContent: content },
    })),
  setContentAnalysis: (analysis) =>
    set((state) => ({
      linkedin: { ...state.linkedin, contentAnalysis: analysis },
    })),
  setRepurposedContent: (content) =>
    set((state) => ({
      linkedin: { ...state.linkedin, repurposedContent: content },
    })),
  setSuggestedHashtags: (hashtags) =>
    set((state) => ({
      linkedin: { ...state.linkedin, suggestedHashtags: hashtags },
    })),
  setImageContext: (context) =>
    set((state) => ({
      linkedin: { ...state.linkedin, imageContext: context },
    })),
  setTargetStyle: (style) =>
    set((state) => ({
      linkedin: { ...state.linkedin, targetStyle: style },
    })),
  setTargetFormat: (format) =>
    set((state) => ({
      linkedin: { ...state.linkedin, targetFormat: format },
    })),
  setIsAnalyzingLinkedIn: (value) =>
    set((state) => ({
      linkedin: { ...state.linkedin, isAnalyzingLinkedIn: value },
    })),
  setIsRepurposing: (value) =>
    set((state) => ({
      linkedin: { ...state.linkedin, isRepurposing: value },
    })),
  setLinkedInError: (error) =>
    set((state) => ({
      linkedin: { ...state.linkedin, linkedInError: error },
    })),
  resetLinkedIn: () =>
    set({ linkedin: initialLinkedInState }),
}))
