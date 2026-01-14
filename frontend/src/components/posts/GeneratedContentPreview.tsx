import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Copy, Check, RefreshCw, Loader2, ImageIcon, ChevronDown, ChevronUp } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { useClipboard } from "@/hooks/useClipboard"
import { ImageGenerationPanel } from "./ImageGenerationPanel"
import { useAppStore } from "@/store/appStore"

interface GeneratedContentPreviewProps {
  content: string
  style: string
  isRegenerating?: boolean
  onRegenerate?: () => void
}

const styleLabels: Record<string, string> = {
  "problem-solution": "Problem-Solution",
  "tips-learnings": "Tips & Learnings",
  "technical-showcase": "Technical Showcase",
}

export function GeneratedContentPreview({
  content,
  style,
  isRegenerating = false,
  onRegenerate,
}: GeneratedContentPreviewProps) {
  const { copied, copy } = useClipboard()
  const { geminiAuth } = useAppStore()
  const [showImageGen, setShowImageGen] = useState(false)

  const handleCopy = () => {
    copy(content)
  }

  const characterCount = content.length
  const isLongPost = characterCount > 3000
  const geminiConnected = geminiAuth.isConnected

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-4"
    >
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              AI Generated Post
            </CardTitle>
            <Badge variant="secondary">
              {styleLabels[style] || style}
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="relative">
            <Textarea
              value={content}
              readOnly
              className="min-h-[300px] font-mono text-sm resize-none"
            />
            {isRegenerating && (
              <div className="absolute inset-0 bg-background/80 flex items-center justify-center rounded-md">
                <div className="flex items-center gap-2 text-muted-foreground">
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>Regenerating...</span>
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={`text-sm ${isLongPost ? "text-amber-600" : "text-muted-foreground"}`}>
                {characterCount} characters
              </span>
              {isLongPost && (
                <span className="text-xs text-amber-600">
                  (LinkedIn limit: 3000)
                </span>
              )}
            </div>

            <div className="flex gap-2">
              {onRegenerate && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onRegenerate}
                  disabled={isRegenerating}
                >
                  {isRegenerating ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCw className="h-4 w-4" />
                  )}
                  Regenerate
                </Button>
              )}
              <Button size="sm" onClick={handleCopy} disabled={isRegenerating}>
                {copied ? (
                  <>
                    <Check className="h-4 w-4" />
                    Copied!
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4" />
                    Copy Post
                  </>
                )}
              </Button>
            </div>
          </div>

          {/* Image Generation Toggle */}
          <div className="pt-2 border-t">
            <Button
              variant="outline"
              className="w-full justify-between"
              onClick={() => setShowImageGen(!showImageGen)}
            >
              <span className="flex items-center gap-2">
                <ImageIcon className="h-4 w-4" />
                {geminiConnected ? "Generate Image for Post" : "Add Image (Connect Gemini)"}
              </span>
              {showImageGen ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Image Generation Panel - Collapsible */}
      <AnimatePresence>
        {showImageGen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
          >
            <ImageGenerationPanel postContent={content} compact />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Next Steps - Only show when image generation is hidden */}
      <AnimatePresence>
        {!showImageGen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="bg-muted/50 rounded-lg p-4 text-sm"
          >
            <h4 className="font-medium mb-2">Next Steps:</h4>
            <ol className="list-decimal list-inside space-y-1 text-muted-foreground">
              <li>Review and edit the generated content as needed</li>
              <li>Click &quot;Copy Post&quot; to copy to clipboard</li>
              <li>Optionally generate an image to accompany your post</li>
              <li>Paste directly into LinkedIn&apos;s post composer and publish!</li>
            </ol>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
