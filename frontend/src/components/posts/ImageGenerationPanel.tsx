import { useState, useCallback } from "react"
import {
  ImageIcon,
  AlertCircle,
  Clock,
  RefreshCw,
  Loader2,
  X,
  CheckCircle2,
} from "lucide-react"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useAppStore } from "@/store/appStore"
import { api, ApiError } from "@/lib/api"
import { useCountdown } from "@/hooks/useCountdown"

// Image styles from backend - matches ImageStyle enum
const IMAGE_STYLES = [
  { id: "infographic", label: "Infographic", description: "Data-driven visual layouts" },
  { id: "minimalist", label: "Minimalist", description: "Clean, simple designs" },
  { id: "conceptual", label: "Conceptual", description: "Abstract idea representation" },
  { id: "abstract", label: "Abstract", description: "Non-representational art" },
  { id: "photorealistic", label: "Photorealistic", description: "Photo-like imagery" },
  { id: "illustrated", label: "Illustrated", description: "Hand-drawn aesthetics" },
  { id: "diagram", label: "Diagram", description: "Technical flowcharts" },
  { id: "gradient", label: "Gradient", description: "Smooth color transitions" },
  { id: "flat_design", label: "Flat Design", description: "2D minimal style" },
  { id: "isometric", label: "Isometric", description: "3D perspective design" },
  { id: "tech_themed", label: "Tech Themed", description: "Technology-focused visuals" },
  { id: "professional", label: "Professional", description: "Corporate business style" },
] as const

type ImageStyleId = (typeof IMAGE_STYLES)[number]["id"]

// LinkedIn-optimized image dimensions - matches ImageDimensions enum
const IMAGE_DIMENSIONS = [
  { id: "1200x627", label: "Link Post", description: "1200x627 - Standard link preview", width: 1200, height: 627 },
  { id: "1080x1080", label: "Square", description: "1080x1080 - Square format", width: 1080, height: 1080 },
  { id: "1200x1200", label: "Large Square", description: "1200x1200 - Large square", width: 1200, height: 1200 },
] as const

type ImageDimensionId = (typeof IMAGE_DIMENSIONS)[number]["id"]

interface ImageGenerationPanelProps {
  postContent: string
}

interface GeneratedImage {
  imageBase64: string
  contentType: string
  style: string
  dimensions: string
}

export function ImageGenerationPanel({ postContent }: ImageGenerationPanelProps) {
  const { geminiAuth } = useAppStore()
  const countdown = useCountdown()

  // Style selection state
  const [selectedStyle, setSelectedStyle] = useState<ImageStyleId | null>(null)
  const [recommendedStyles, setRecommendedStyles] = useState<string[]>([])

  // Dimension selection state
  const [selectedDimension, setSelectedDimension] = useState<ImageDimensionId>("1200x627")

  // Generation state
  const [isGenerating, setIsGenerating] = useState(false)
  const [generatedImage, setGeneratedImage] = useState<GeneratedImage | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isRetryable, setIsRetryable] = useState(false)

  // Abort controller for cancellation
  const [abortController, setAbortController] = useState<AbortController | null>(null)

  const geminiConnected = geminiAuth.isConnected

  const handleStyleSelect = useCallback((styleId: ImageStyleId) => {
    setSelectedStyle(styleId)
    setError(null)
    setIsRetryable(false)
  }, [])

  const handleDimensionSelect = useCallback((dimensionId: ImageDimensionId) => {
    setSelectedDimension(dimensionId)
    setError(null)
    setIsRetryable(false)
  }, [])

  const handleGenerate = useCallback(async () => {
    if (!geminiConnected) {
      setError("Please connect your Gemini API key first.")
      setIsRetryable(false)
      return
    }

    if (!postContent.trim()) {
      setError("No post content provided for image generation.")
      setIsRetryable(false)
      return
    }

    // Don't allow generation during rate limit countdown
    if (countdown.isActive) {
      return
    }

    // Create abort controller for cancellation
    const controller = new AbortController()
    setAbortController(controller)

    setIsGenerating(true)
    setError(null)
    setIsRetryable(false)
    countdown.reset()

    try {
      const response = await api.generateImage({
        postContent,
        style: selectedStyle || undefined,
        dimensions: selectedDimension,
      })

      if (response.success && response.image_base64) {
        setGeneratedImage({
          imageBase64: response.image_base64,
          contentType: response.content_type || "unknown",
          style: response.recommended_style || selectedStyle || "unknown",
          dimensions: response.dimensions || selectedDimension,
        })

        // Update recommended styles from response
        if (response.recommended_style) {
          setRecommendedStyles((prev) => {
            if (!prev.includes(response.recommended_style!)) {
              return [response.recommended_style!, ...prev.slice(0, 2)]
            }
            return prev
          })
        }
      } else {
        setError(response.error || "Failed to generate image. Please try again.")
        setIsRetryable(true)
        if (response.retry_after) {
          countdown.start(response.retry_after)
        }
      }
    } catch (err) {
      // Check for abort
      if (err instanceof Error && err.name === "AbortError") {
        // Generation was cancelled
        return
      }

      // Handle ApiError with retryable flag
      if (err instanceof ApiError) {
        setError(err.message)
        setIsRetryable(err.retryable)
        if (err.retryAfter) {
          countdown.start(err.retryAfter)
        }
      } else {
        const errorMessage =
          err instanceof Error
            ? err.message
            : "Something went wrong. Please try again."
        setError(errorMessage)
        setIsRetryable(true)
      }
    } finally {
      setIsGenerating(false)
      setAbortController(null)
    }
  }, [postContent, selectedStyle, selectedDimension, geminiConnected, countdown])

  const handleCancel = useCallback(() => {
    if (abortController) {
      abortController.abort()
      setAbortController(null)
    }
    setIsGenerating(false)
  }, [abortController])

  const handleRegenerate = useCallback(() => {
    setGeneratedImage(null)
    handleGenerate()
  }, [handleGenerate])

  // Get dimension preview aspect ratio
  const selectedDimensionInfo = IMAGE_DIMENSIONS.find((d) => d.id === selectedDimension)
  const aspectRatio = selectedDimensionInfo
    ? selectedDimensionInfo.width / selectedDimensionInfo.height
    : 1.91

  // If Gemini is not connected, show connect prompt
  if (!geminiConnected) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <ImageIcon className="h-5 w-5" />
            Image Generation
          </CardTitle>
          <CardDescription>Generate images for your LinkedIn post</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center space-y-4">
            <ImageIcon className="h-12 w-12 text-muted-foreground" />
            <div className="space-y-2">
              <p className="font-medium">Connect Gemini to Generate Images</p>
              <p className="text-sm text-muted-foreground">
                Connect your Gemini API key to enable AI-powered image generation.
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
          <ImageIcon className="h-5 w-5" />
          Image Generation
        </CardTitle>
        <CardDescription>
          Generate professional images for your LinkedIn post using Gemini
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Style Selection */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium">Image Style</h4>
            {recommendedStyles.length > 0 && (
              <span className="text-xs text-muted-foreground">
                Recommended based on content
              </span>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            {IMAGE_STYLES.map((style) => {
              const isRecommended = recommendedStyles.includes(style.id)
              const isSelected = selectedStyle === style.id
              return (
                <Button
                  key={style.id}
                  variant={isSelected ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleStyleSelect(style.id)}
                  disabled={isGenerating}
                  className="relative"
                  title={style.description}
                  aria-label={`Select ${style.label} style`}
                  aria-pressed={isSelected}
                >
                  {style.label}
                  {isRecommended && !isSelected && (
                    <Badge
                      variant="secondary"
                      className="absolute -top-2 -right-2 h-4 text-[10px] px-1"
                    >
                      AI
                    </Badge>
                  )}
                </Button>
              )
            })}
          </div>
          {selectedStyle && (
            <p className="text-xs text-muted-foreground">
              {IMAGE_STYLES.find((s) => s.id === selectedStyle)?.description}
            </p>
          )}
        </div>

        {/* Dimension Selection */}
        <div className="space-y-3">
          <h4 className="text-sm font-medium">Image Dimensions</h4>
          <div className="grid grid-cols-3 gap-3">
            {IMAGE_DIMENSIONS.map((dimension) => {
              const isSelected = selectedDimension === dimension.id
              return (
                <button
                  key={dimension.id}
                  onClick={() => handleDimensionSelect(dimension.id)}
                  disabled={isGenerating}
                  className={`
                    p-3 rounded-lg border-2 transition-all text-left
                    ${
                      isSelected
                        ? "border-primary bg-primary/5"
                        : "border-border hover:border-primary/50"
                    }
                    ${isGenerating ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}
                  `}
                  aria-label={`Select ${dimension.label} dimensions (${dimension.id})`}
                  aria-pressed={isSelected}
                >
                  <div className="space-y-2">
                    <div
                      className={`
                        w-full bg-muted rounded border
                        ${isSelected ? "border-primary/50" : "border-border"}
                      `}
                      style={{ aspectRatio: dimension.width / dimension.height }}
                    />
                    <div>
                      <p className="text-sm font-medium">{dimension.label}</p>
                      <p className="text-xs text-muted-foreground">{dimension.id}</p>
                    </div>
                  </div>
                  {isSelected && (
                    <CheckCircle2 className="absolute top-2 right-2 h-4 w-4 text-primary" />
                  )}
                </button>
              )
            })}
          </div>
        </div>

        {/* Dimension Preview */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium">Preview</h4>
          <div
            className="w-full max-w-md mx-auto bg-muted/50 rounded-lg border border-dashed border-border flex items-center justify-center"
            style={{ aspectRatio }}
          >
            {generatedImage ? (
              <img
                src={`data:image/png;base64,${generatedImage.imageBase64}`}
                alt="Generated LinkedIn post image"
                className="w-full h-full object-contain rounded-lg"
              />
            ) : isGenerating ? (
              <div className="flex flex-col items-center gap-2 text-muted-foreground">
                <Loader2 className="h-8 w-8 animate-spin" />
                <span className="text-sm">Generating image...</span>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2 text-muted-foreground p-4">
                <ImageIcon className="h-8 w-8" />
                <span className="text-sm text-center">
                  {selectedDimensionInfo?.description || "Select dimensions"}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Generate Button */}
        <div className="flex justify-center gap-2">
          {isGenerating ? (
            <Button variant="destructive" onClick={handleCancel} className="gap-2">
              <X className="h-4 w-4" />
              Cancel
            </Button>
          ) : generatedImage ? (
            <Button onClick={handleRegenerate} disabled={countdown.isActive} className="gap-2">
              <RefreshCw className="h-4 w-4" />
              {countdown.isActive ? `Wait ${countdown.secondsLeft}s` : "Regenerate"}
            </Button>
          ) : (
            <Button
              onClick={handleGenerate}
              disabled={countdown.isActive || !postContent.trim()}
              className="gap-2"
            >
              <ImageIcon className="h-4 w-4" />
              {countdown.isActive ? `Wait ${countdown.secondsLeft}s` : "Generate Image"}
            </Button>
          )}
        </div>

        {/* Loading State with Spinner */}
        {isGenerating && (
          <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Generating with Gemini...</span>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="flex items-start gap-2 text-destructive bg-destructive/10 p-3 rounded-md">
            <AlertCircle className="h-5 w-5 mt-0.5 shrink-0" />
            <div className="flex-1">
              <p className="text-sm">{error}</p>
              {/* Rate Limit Countdown */}
              {countdown.isActive && countdown.secondsLeft > 0 && (
                <div className="flex items-center gap-2 mt-2 text-xs">
                  <Clock className="h-4 w-4" />
                  <span>
                    Retry available in {countdown.secondsLeft} second
                    {countdown.secondsLeft !== 1 ? "s" : ""}
                  </span>
                </div>
              )}
              {/* Retry Button */}
              {isRetryable && !countdown.isActive && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="mt-2 h-8"
                  onClick={() => {
                    setError(null)
                    setIsRetryable(false)
                    handleGenerate()
                  }}
                >
                  <RefreshCw className="h-4 w-4" />
                  Try Again
                </Button>
              )}
              {/* Dismiss Button */}
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="mt-2 h-8 px-2 ml-2"
                onClick={() => {
                  setError(null)
                  setIsRetryable(false)
                  countdown.reset()
                }}
              >
                Dismiss
              </Button>
            </div>
          </div>
        )}

        {/* Generated Image Info */}
        {generatedImage && (
          <div className="text-xs text-muted-foreground text-center space-y-1">
            <p>
              Style: <span className="font-medium">{generatedImage.style}</span> |
              Dimensions: <span className="font-medium">{generatedImage.dimensions}</span>
            </p>
            <p>
              Content Type: <span className="font-medium">{generatedImage.contentType}</span>
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
