import { motion } from "framer-motion"
import { Loader2, Sparkles } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { useAppStore } from "@/store/appStore"
import { useRepurposeContent } from "@/hooks/useLinkedInRepurpose"
import type { RepurposeStyle, RepurposeFormat } from "@/lib/api"

const STYLE_OPTIONS: { value: RepurposeStyle; label: string; description: string }[] = [
  { value: "same", label: "Keep Original Tone", description: "Preserve the author's voice and style" },
  { value: "professional", label: "More Professional", description: "Formal, thought-leader tone" },
  { value: "casual", label: "More Conversational", description: "Friendly, approachable language" },
  { value: "storytelling", label: "Storytelling Focus", description: "Narrative-driven, engaging hook" },
]

const FORMAT_OPTIONS: { value: RepurposeFormat; label: string; description: string }[] = [
  { value: "expanded", label: "Expand", description: "Add depth and context (1500-2500 chars)" },
  { value: "condensed", label: "Condense", description: "Key points only (500-800 chars)" },
  { value: "thread", label: "Thread Format", description: "Numbered list structure" },
]

export function RepurposeOptions() {
  const {
    linkedin,
    claudeAuth,
    openaiAuth,
    setTargetStyle,
    setTargetFormat,
  } = useAppStore()
  const repurposeContent = useRepurposeContent()

  const handleRepurpose = () => {
    // Determine which provider to use (prefer Claude if both connected)
    const provider = claudeAuth.isConnected ? "claude" : "openai"
    repurposeContent.mutate({ provider })
  }

  const hasAnalysis = linkedin.contentAnalysis !== null
  const hasProvider = claudeAuth.isConnected || openaiAuth.isConnected

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <span className="text-2xl bg-gradient-to-br from-primary to-primary/60 bg-clip-text text-transparent">2</span>
          <Sparkles className="h-5 w-5 text-muted-foreground" />
          Repurpose Options
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-3">
          <Label className="text-sm font-medium">Target Style</Label>
          <RadioGroup
            value={linkedin.targetStyle}
            onValueChange={(v) => setTargetStyle(v as RepurposeStyle)}
            className="grid gap-2"
            disabled={!hasAnalysis}
          >
            {STYLE_OPTIONS.map((option) => (
              <Label
                key={option.value}
                htmlFor={`style-${option.value}`}
                className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                  linkedin.targetStyle === option.value
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-primary/50"
                } ${!hasAnalysis ? "opacity-50 cursor-not-allowed" : ""}`}
              >
                <RadioGroupItem value={option.value} id={`style-${option.value}`} />
                <div className="flex-1">
                  <span className="font-medium text-sm">{option.label}</span>
                  <p className="text-xs text-muted-foreground">{option.description}</p>
                </div>
              </Label>
            ))}
          </RadioGroup>
        </div>

        <div className="space-y-3">
          <Label className="text-sm font-medium">Output Format</Label>
          <RadioGroup
            value={linkedin.targetFormat}
            onValueChange={(v) => setTargetFormat(v as RepurposeFormat)}
            className="grid gap-2"
            disabled={!hasAnalysis}
          >
            {FORMAT_OPTIONS.map((option) => (
              <Label
                key={option.value}
                htmlFor={`format-${option.value}`}
                className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                  linkedin.targetFormat === option.value
                    ? "border-primary bg-primary/5"
                    : "border-border hover:border-primary/50"
                } ${!hasAnalysis ? "opacity-50 cursor-not-allowed" : ""}`}
              >
                <RadioGroupItem value={option.value} id={`format-${option.value}`} />
                <div className="flex-1">
                  <span className="font-medium text-sm">{option.label}</span>
                  <p className="text-xs text-muted-foreground">{option.description}</p>
                </div>
              </Label>
            ))}
          </RadioGroup>
        </div>

        <motion.div
          initial={false}
          animate={{ opacity: hasAnalysis ? 1 : 0.5 }}
        >
          <Button
            onClick={handleRepurpose}
            disabled={!hasAnalysis || !hasProvider || linkedin.isRepurposing}
            className="w-full"
            size="lg"
          >
            {linkedin.isRepurposing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Repurposing...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Repurpose Content
              </>
            )}
          </Button>
          {!hasProvider && hasAnalysis && (
            <p className="text-xs text-muted-foreground text-center mt-2">
              Connect an AI provider above to repurpose content
            </p>
          )}
          {!hasAnalysis && (
            <p className="text-xs text-muted-foreground text-center mt-2">
              Analyze content first to enable repurposing
            </p>
          )}
        </motion.div>
      </CardContent>
    </Card>
  )
}
