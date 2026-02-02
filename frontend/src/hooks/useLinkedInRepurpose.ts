import { useMutation } from "@tanstack/react-query"
import { api } from "@/lib/api"
import { useAppStore } from "@/store/appStore"
import type { RepurposeStyle, RepurposeFormat, AIProvider } from "@/lib/api"

export function useAnalyzeLinkedIn() {
  const {
    setContentAnalysis,
    setIsAnalyzingLinkedIn,
    setLinkedInError,
  } = useAppStore()

  return useMutation({
    mutationFn: async (content: string) => {
      setIsAnalyzingLinkedIn(true)
      setLinkedInError(null)
      const response = await api.analyzeLinkedIn(content)
      if (!response.success) {
        throw new Error(response.error || "Analysis failed")
      }
      return response.data!
    },
    onSuccess: (data) => {
      setContentAnalysis(data)
      setIsAnalyzingLinkedIn(false)
    },
    onError: (error: Error) => {
      setLinkedInError(error.message)
      setIsAnalyzingLinkedIn(false)
    },
  })
}

interface RepurposeParams {
  targetStyle?: RepurposeStyle
  targetFormat?: RepurposeFormat
  provider?: AIProvider
}

export function useRepurposeContent() {
  const {
    linkedin,
    claudeAuth,
    openaiAuth,
    setRepurposedContent,
    setSuggestedHashtags,
    setImageContext,
    setIsRepurposing,
    setLinkedInError,
  } = useAppStore()

  return useMutation({
    mutationFn: async (params: RepurposeParams = {}) => {
      if (!linkedin.contentAnalysis) {
        throw new Error("No content analysis available. Please analyze content first.")
      }

      // Determine provider: use param, or detect from connected providers
      const provider = params.provider || (claudeAuth.isConnected ? "claude" : "openai")

      setIsRepurposing(true)
      setLinkedInError(null)

      const response = await api.repurposeContent(
        linkedin.originalContent,
        linkedin.contentAnalysis,
        params.targetStyle || linkedin.targetStyle,
        params.targetFormat || linkedin.targetFormat,
        provider
      )

      if (!response.success) {
        throw new Error(response.error || "Repurpose failed")
      }

      return response
    },
    onSuccess: (data) => {
      setRepurposedContent(data.repurposed_content || null)
      setSuggestedHashtags(data.suggested_hashtags || [])
      setImageContext(data.image_context || null)
      setIsRepurposing(false)
    },
    onError: (error: Error) => {
      setLinkedInError(error.message)
      setIsRepurposing(false)
    },
  })
}
