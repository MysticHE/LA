import { useEffect } from "react"
import { Copy, Check, RefreshCw, Loader2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Skeleton } from "@/components/ui/skeleton"
import { useAppStore } from "@/store/appStore"
import { useGeneratePrompt } from "@/hooks/useAnalyzeRepo"
import { useClipboard } from "@/hooks/useClipboard"

const POST_STYLES = [
  { id: "problem-solution", label: "Problem-Solution" },
  { id: "tips-learnings", label: "Tips & Learnings" },
  { id: "technical-showcase", label: "Technical Showcase" },
] as const

export function PostCard() {
  const {
    analysis,
    selectedStyle,
    setSelectedStyle,
    generatedPrompts,
    isGenerating,
  } = useAppStore()
  const generatePrompt = useGeneratePrompt()
  const { copied, copy } = useClipboard()

  const currentPrompt = generatedPrompts[selectedStyle]

  useEffect(() => {
    if (analysis && !currentPrompt && !isGenerating) {
      generatePrompt.mutate(selectedStyle)
    }
  }, [analysis, selectedStyle, currentPrompt, isGenerating])

  if (!analysis) {
    return null
  }

  const handleStyleChange = (value: string) => {
    const style = value as typeof selectedStyle
    setSelectedStyle(style)
    if (!generatedPrompts[style]) {
      generatePrompt.mutate(style)
    }
  }

  const handleRegenerate = () => {
    generatePrompt.mutate(selectedStyle)
  }

  const handleCopy = () => {
    if (currentPrompt?.prompt) {
      copy(currentPrompt.prompt)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <span className="text-2xl">3</span>
          Generated LinkedIn Post Prompt
        </CardTitle>
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
            <TabsContent key={style.id} value={style.id}>
              {isGenerating && !generatedPrompts[style.id] ? (
                <div className="space-y-3">
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-4/5" />
                  <Skeleton className="h-4 w-3/4" />
                  <Skeleton className="h-32 w-full" />
                </div>
              ) : generatedPrompts[style.id] ? (
                <div className="space-y-4">
                  <Textarea
                    value={generatedPrompts[style.id]?.prompt || ""}
                    readOnly
                    className="min-h-[300px] font-mono text-sm"
                  />
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-muted-foreground">
                      {generatedPrompts[style.id]?.prompt.length || 0} characters
                    </span>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleRegenerate}
                        disabled={isGenerating}
                      >
                        {isGenerating ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <RefreshCw className="h-4 w-4" />
                        )}
                        Regenerate
                      </Button>
                      <Button size="sm" onClick={handleCopy}>
                        {copied ? (
                          <>
                            <Check className="h-4 w-4" />
                            Copied!
                          </>
                        ) : (
                          <>
                            <Copy className="h-4 w-4" />
                            Copy Prompt
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="py-8 text-center text-muted-foreground">
                  Click to generate prompt
                </div>
              )}
            </TabsContent>
          ))}
        </Tabs>

        {currentPrompt?.instructions && (
          <div className="bg-muted/50 rounded-lg p-4 text-sm">
            <h4 className="font-medium mb-2">How to use:</h4>
            <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
              <li>Copy the prompt above</li>
              <li>
                Open Claude Code CLI: <code className="bg-muted px-1 rounded">claude</code>
              </li>
              <li>Paste the prompt and press Enter</li>
              <li>Review and edit the generated LinkedIn post</li>
              <li>Copy the final post to LinkedIn</li>
            </ol>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
