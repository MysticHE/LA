import { useState, useCallback } from "react"
import { Sparkles, AlertCircle, Key } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { useAppStore } from "@/store/appStore"
import { api, type AnalysisResult, type AIGenerateResponse } from "@/lib/api"
import { GeneratedContentPreview } from "./GeneratedContentPreview"

const POST_STYLES = [
  { id: "problem-solution", label: "Problem-Solution" },
  { id: "tips-learnings", label: "Tips & Learnings" },
  { id: "technical-showcase", label: "Technical Showcase" },
] as const

type PostStyle = (typeof POST_STYLES)[number]["id"]

interface AIPostGeneratorProps {
  analysis: AnalysisResult
}

interface GeneratedContent {
  content: string
  style: string
}

export function AIPostGenerator({ analysis }: AIPostGeneratorProps) {
  const { claudeAuth } = useAppStore()

  const [selectedStyle, setSelectedStyle] = useState<PostStyle>("problem-solution")
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedContents, setGeneratedContents] = useState<Record<PostStyle, GeneratedContent | null>>({
    "problem-solution": null,
    "tips-learnings": null,
    "technical-showcase": null,
  })
  const [error, setError] = useState<string | null>(null)
  const [retryAfter, setRetryAfter] = useState<number | null>(null)

  const handleGenerate = useCallback(async (style: PostStyle) => {
    if (!claudeAuth.isConnected) {
      setError("Please connect your Claude API key first.")
      return
    }

    setIsGenerating(true)
    setError(null)
    setRetryAfter(null)

    try {
      const response: AIGenerateResponse = await api.generateAIPost(analysis, style)

      if (response.success && response.content) {
        setGeneratedContents((prev) => ({
          ...prev,
          [style]: {
            content: response.content!,
            style: response.style || style,
          },
        }))
      } else {
        setError(response.error || "Failed to generate content. Please try again.")
        if (response.retry_after) {
          setRetryAfter(response.retry_after)
        }
      }
    } catch (err) {
      const errorMessage = err instanceof Error
        ? err.message
        : "Network error. Please check your connection and try again."
      setError(errorMessage)
    } finally {
      setIsGenerating(false)
    }
  }, [analysis, claudeAuth.isConnected])

  const handleStyleChange = (value: string) => {
    setSelectedStyle(value as PostStyle)
    setError(null)
    setRetryAfter(null)
  }

  const handleRegenerate = () => {
    handleGenerate(selectedStyle)
  }

  // If Claude is not connected, show connect prompt
  if (!claudeAuth.isConnected) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            AI Post Generator
          </CardTitle>
          <CardDescription>
            Generate LinkedIn posts using Claude AI
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center space-y-4">
            <Key className="h-12 w-12 text-muted-foreground" />
            <div className="space-y-2">
              <p className="font-medium">Connect Claude to Generate Posts</p>
              <p className="text-sm text-muted-foreground">
                Connect your Anthropic API key to enable AI-powered post generation.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Sparkles className="h-5 w-5" />
          AI Post Generator
        </CardTitle>
        <CardDescription>
          Generate LinkedIn posts using Claude AI based on your repository analysis
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Tabs value={selectedStyle} onValueChange={handleStyleChange}>
          <TabsList className="grid w-full grid-cols-3">
            {POST_STYLES.map((style) => (
              <TabsTrigger key={style.id} value={style.id}>
                {style.label}
              </TabsTrigger>
            ))}
          </TabsList>

          {POST_STYLES.map((style) => (
            <TabsContent key={style.id} value={style.id} className="space-y-4">
              {/* Loading State */}
              {isGenerating && selectedStyle === style.id && !generatedContents[style.id] && (
                <div className="space-y-4">
                  <div className="space-y-3">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-4/5" />
                    <Skeleton className="h-4 w-3/4" />
                  </div>
                  <Skeleton className="h-[200px] w-full" />
                  <div className="space-y-3">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-2/3" />
                  </div>
                </div>
              )}

              {/* Generated Content */}
              {generatedContents[style.id] && (
                <GeneratedContentPreview
                  content={generatedContents[style.id]!.content}
                  style={generatedContents[style.id]!.style}
                  isRegenerating={isGenerating && selectedStyle === style.id}
                  onRegenerate={handleRegenerate}
                />
              )}

              {/* Generate Button (when no content and not loading) */}
              {!generatedContents[style.id] && !(isGenerating && selectedStyle === style.id) && (
                <div className="flex flex-col items-center justify-center py-8 space-y-4">
                  <p className="text-muted-foreground text-center">
                    Generate a {style.label.toLowerCase()} style LinkedIn post based on your repository.
                  </p>
                  <Button
                    onClick={() => handleGenerate(style.id)}
                    disabled={isGenerating}
                  >
                    <Sparkles className="h-4 w-4" />
                    Generate Post
                  </Button>
                </div>
              )}
            </TabsContent>
          ))}
        </Tabs>

        {/* Error Display */}
        {error && (
          <div className="flex items-start gap-2 text-destructive bg-destructive/10 p-3 rounded-md">
            <AlertCircle className="h-5 w-5 mt-0.5 shrink-0" />
            <div className="flex-1">
              <p className="text-sm">{error}</p>
              {retryAfter && (
                <p className="text-xs mt-1">
                  Please wait {retryAfter} seconds before trying again.
                </p>
              )}
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="mt-2 h-8 px-2"
                onClick={() => {
                  setError(null)
                  setRetryAfter(null)
                }}
              >
                Dismiss
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
