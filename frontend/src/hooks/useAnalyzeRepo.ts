import { useMutation } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { useAppStore } from "@/store/appStore"

export function useAnalyzeRepo() {
  const { setAnalysis, setIsAnalyzing, setError } = useAppStore()

  return useMutation({
    mutationFn: async (url: string) => {
      setIsAnalyzing(true)
      setError(null)
      const response = await api.analyzeRepo(url)
      if (!response.success) {
        throw new Error(response.error || "Analysis failed")
      }
      return response.data!
    },
    onSuccess: (data) => {
      setAnalysis(data)
      setIsAnalyzing(false)
    },
    onError: (error: Error) => {
      setError(error.message)
      setIsAnalyzing(false)
    },
  })
}

export function useGeneratePrompt() {
  const { analysis, setGeneratedPrompt, setIsGenerating, setError } =
    useAppStore()

  return useMutation({
    mutationFn: async (style: string) => {
      if (!analysis) throw new Error("No analysis available")
      setIsGenerating(true)
      setError(null)
      const response = await api.generatePrompt(analysis, style)
      if (!response.success) {
        throw new Error(response.error || "Generation failed")
      }
      return { style, prompt: response.data! }
    },
    onSuccess: ({ style, prompt }) => {
      setGeneratedPrompt(
        style as "problem-solution" | "tips-learnings" | "technical-showcase",
        prompt
      )
      setIsGenerating(false)
    },
    onError: (error: Error) => {
      setError(error.message)
      setIsGenerating(false)
    },
  })
}
