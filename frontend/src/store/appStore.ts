import { create } from "zustand"
import type { AnalysisResult, GeneratedPrompt } from "@/lib/api"

type PostStyle = "problem-solution" | "tips-learnings" | "technical-showcase"

interface AppState {
  repoUrl: string
  analysis: AnalysisResult | null
  selectedStyle: PostStyle
  generatedPrompts: Record<PostStyle, GeneratedPrompt | null>
  isAnalyzing: boolean
  isGenerating: boolean
  error: string | null

  setRepoUrl: (url: string) => void
  setAnalysis: (result: AnalysisResult | null) => void
  setSelectedStyle: (style: PostStyle) => void
  setGeneratedPrompt: (style: PostStyle, prompt: GeneratedPrompt) => void
  setIsAnalyzing: (value: boolean) => void
  setIsGenerating: (value: boolean) => void
  setError: (error: string | null) => void
  reset: () => void
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
}))
