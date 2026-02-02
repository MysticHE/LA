import { useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { Copy, Check, Image, Hash, ArrowRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { useAppStore } from "@/store/appStore"

export function ContentPreview() {
  const { linkedin, setRepurposedContent } = useAppStore()
  const [copied, setCopied] = useState(false)
  const [showOriginal, setShowOriginal] = useState(false)

  if (!linkedin.repurposedContent) {
    return null
  }

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(linkedin.repurposedContent || "")
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      console.error("Failed to copy")
    }
  }

  const charCount = linkedin.repurposedContent.length

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
    >
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-lg flex items-center gap-2">
            <span className="text-2xl bg-gradient-to-br from-primary to-primary/60 bg-clip-text text-transparent">3</span>
            Repurposed Content
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowOriginal(!showOriginal)}
              className="text-xs"
            >
              {showOriginal ? "Hide Original" : "Compare with Original"}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopy}
              className="gap-1.5"
            >
              {copied ? (
                <>
                  <Check className="h-4 w-4 text-green-500" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="h-4 w-4" />
                  Copy
                </>
              )}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <AnimatePresence mode="wait">
            {showOriginal ? (
              <motion.div
                key="comparison"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="grid md:grid-cols-2 gap-4"
              >
                <div className="space-y-2">
                  <h4 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                    Original
                    <ArrowRight className="h-3 w-3" />
                  </h4>
                  <div className="p-3 rounded-lg bg-muted/50 text-sm whitespace-pre-wrap max-h-[300px] overflow-y-auto">
                    {linkedin.originalContent}
                  </div>
                </div>
                <div className="space-y-2">
                  <h4 className="text-sm font-medium text-primary">Repurposed</h4>
                  <Textarea
                    value={linkedin.repurposedContent}
                    onChange={(e) => setRepurposedContent(e.target.value)}
                    className="min-h-[300px] resize-none"
                  />
                </div>
              </motion.div>
            ) : (
              <motion.div
                key="single"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <Textarea
                  value={linkedin.repurposedContent}
                  onChange={(e) => setRepurposedContent(e.target.value)}
                  className="min-h-[250px] resize-none"
                />
              </motion.div>
            )}
          </AnimatePresence>

          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{charCount.toLocaleString()} characters</span>
            {linkedin.contentAnalysis && (
              <span className="flex items-center gap-1">
                <span className="capitalize">{linkedin.targetStyle}</span>
                <span>•</span>
                <span className="capitalize">{linkedin.targetFormat}</span>
              </span>
            )}
          </div>

          {linkedin.suggestedHashtags.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium flex items-center gap-1.5">
                <Hash className="h-4 w-4 text-muted-foreground" />
                Suggested Hashtags
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {linkedin.suggestedHashtags.map((tag) => (
                  <button
                    key={tag}
                    onClick={() => {
                      const hashtag = `#${tag}`
                      if (!linkedin.repurposedContent?.includes(hashtag)) {
                        setRepurposedContent(
                          (linkedin.repurposedContent || "") + `\n\n${hashtag}`
                        )
                      }
                    }}
                    className="px-2 py-1 bg-primary/10 hover:bg-primary/20 text-primary text-xs rounded-full transition-colors"
                  >
                    #{tag}
                  </button>
                ))}
              </div>
            </div>
          )}

          {linkedin.imageContext && (
            <div className="pt-4 border-t">
              <Button variant="outline" className="w-full gap-2">
                <Image className="h-4 w-4" />
                Generate Image for This Post
              </Button>
              <p className="text-xs text-muted-foreground text-center mt-2">
                Recommended styles: {linkedin.imageContext.recommended_styles.slice(0, 3).join(", ")}
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}
