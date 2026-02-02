import { AnimatePresence, motion } from "framer-motion"
import { Loader2, Search, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useAppStore } from "@/store/appStore"
import { useAnalyzeLinkedIn } from "@/hooks/useLinkedInRepurpose"

export function LinkedInInputForm() {
  const { linkedin, setOriginalContent } = useAppStore()
  const analyzeLinkedIn = useAnalyzeLinkedIn()

  const handleAnalyze = () => {
    if (linkedin.originalContent.trim().length >= 10) {
      analyzeLinkedIn.mutate(linkedin.originalContent)
    }
  }

  const charCount = linkedin.originalContent.length
  const isValidLength = charCount >= 10 && charCount <= 10000

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <span className="text-2xl bg-gradient-to-br from-primary to-primary/60 bg-clip-text text-transparent">1</span>
          <FileText className="h-5 w-5 text-muted-foreground" />
          Paste LinkedIn Post
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <Textarea
          placeholder="Paste the LinkedIn post content you want to repurpose...

Example: Copy the text from any LinkedIn post and paste it here. The AI will analyze the content and help you create a fresh version with your chosen style and format."
          className="min-h-[200px] resize-none"
          value={linkedin.originalContent}
          onChange={(e) => setOriginalContent(e.target.value)}
          disabled={linkedin.isAnalyzingLinkedIn}
        />

        <div className="flex items-center justify-between">
          <p className={`text-xs ${isValidLength ? "text-muted-foreground" : "text-destructive"}`}>
            {charCount.toLocaleString()} characters
            {charCount < 10 && " (minimum 10)"}
            {charCount > 10000 && " (maximum 10,000)"}
            {isValidLength && " • Recommended: 500-2000"}
          </p>
          <Button
            onClick={handleAnalyze}
            disabled={!isValidLength || linkedin.isAnalyzingLinkedIn}
            className="min-w-[140px]"
          >
            {linkedin.isAnalyzingLinkedIn ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Search className="h-4 w-4" />
                Analyze Content
              </>
            )}
          </Button>
        </div>

        <AnimatePresence>
          {linkedin.linkedInError && (
            <motion.p
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              className="text-sm text-destructive bg-destructive/10 p-3 rounded-md border border-destructive/20"
            >
              {linkedin.linkedInError}
            </motion.p>
          )}
        </AnimatePresence>

        <AnimatePresence>
          {linkedin.contentAnalysis && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              className="p-4 rounded-lg border bg-muted/30 space-y-3"
            >
              <h4 className="font-medium text-sm">Content Analysis</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">Tone:</span>{" "}
                  <span className="capitalize font-medium">{linkedin.contentAnalysis.tone}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Type:</span>{" "}
                  <span className="capitalize font-medium">{linkedin.contentAnalysis.content_type}</span>
                </div>
              </div>
              {linkedin.contentAnalysis.themes.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {linkedin.contentAnalysis.themes.map((theme) => (
                    <span
                      key={theme}
                      className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded-full"
                    >
                      {theme}
                    </span>
                  ))}
                </div>
              )}
              {linkedin.contentAnalysis.key_points.length > 0 && (
                <div className="space-y-1">
                  <span className="text-muted-foreground text-xs">Key Points:</span>
                  <ul className="text-xs space-y-1 list-disc list-inside text-muted-foreground">
                    {linkedin.contentAnalysis.key_points.slice(0, 3).map((point, i) => (
                      <li key={i} className="line-clamp-1">{point}</li>
                    ))}
                  </ul>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </CardContent>
    </Card>
  )
}
