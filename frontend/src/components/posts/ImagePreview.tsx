import { useState, useCallback } from "react"
import {
  Download,
  Copy,
  RefreshCw,
  Check,
  AlertCircle,
  Loader2,
  X,
} from "lucide-react"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useImageDownload } from "@/hooks/useImageDownload"

export interface GeneratedImageData {
  imageBase64: string
  contentType: string
  style: string
  dimensions: string
}

interface ImagePreviewProps {
  /** The generated image data to display */
  image: GeneratedImageData
  /** Alt text for the image for accessibility */
  altText?: string
  /** Callback to trigger regeneration with the same settings */
  onRegenerate?: () => void
  /** Whether regeneration is in progress */
  isRegenerating?: boolean
  /** Callback to close/dismiss the preview */
  onClose?: () => void
}

/**
 * ImagePreview Component
 *
 * Displays a generated image with download, copy, and regenerate functionality.
 * Designed for LinkedIn post images with accessibility support.
 */
export function ImagePreview({
  image,
  altText = "Generated LinkedIn post image",
  onRegenerate,
  isRegenerating = false,
  onClose,
}: ImagePreviewProps) {
  const { download, copyToClipboard, isDownloading, isCopying, downloadError, copyError } =
    useImageDownload()

  // Feedback states for copy/download success
  const [downloadSuccess, setDownloadSuccess] = useState(false)
  const [copySuccess, setCopySuccess] = useState(false)

  // Parse dimensions for display
  const [width, height] = image.dimensions.split("x").map(Number)
  const aspectRatio = width && height ? width / height : 1.91

  const handleDownload = useCallback(async () => {
    const success = await download(image.imageBase64, {
      filename: `linkedin-${image.style}-${image.dimensions}.png`,
    })
    if (success) {
      setDownloadSuccess(true)
      setTimeout(() => setDownloadSuccess(false), 2000)
    }
  }, [download, image.imageBase64, image.style, image.dimensions])

  const handleCopy = useCallback(async () => {
    const success = await copyToClipboard(image.imageBase64)
    if (success) {
      setCopySuccess(true)
      setTimeout(() => setCopySuccess(false), 2000)
    }
  }, [copyToClipboard, image.imageBase64])

  const handleRegenerate = useCallback(() => {
    if (onRegenerate && !isRegenerating) {
      onRegenerate()
    }
  }, [onRegenerate, isRegenerating])

  return (
    <Card className="w-full">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Image Preview</CardTitle>
          {onClose && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              aria-label="Close image preview"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Image Display */}
        <div
          className="w-full mx-auto overflow-hidden rounded-lg border border-border bg-muted/30"
          style={{ aspectRatio }}
        >
          <img
            src={`data:image/png;base64,${image.imageBase64}`}
            alt={altText}
            className="w-full h-full object-contain"
            loading="lazy"
          />
        </div>

        {/* Image Info */}
        <div className="flex flex-wrap gap-2 justify-center text-xs text-muted-foreground">
          <span className="px-2 py-1 bg-muted rounded">
            Style: <span className="font-medium">{image.style}</span>
          </span>
          <span className="px-2 py-1 bg-muted rounded">
            Dimensions: <span className="font-medium">{image.dimensions}</span>
          </span>
          <span className="px-2 py-1 bg-muted rounded">
            Type: <span className="font-medium">{image.contentType}</span>
          </span>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-2 justify-center">
          {/* Download Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleDownload}
            disabled={isDownloading}
            className="gap-2"
            aria-label="Download image as PNG"
          >
            {isDownloading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : downloadSuccess ? (
              <Check className="h-4 w-4 text-green-500" />
            ) : (
              <Download className="h-4 w-4" />
            )}
            {downloadSuccess ? "Downloaded!" : "Download PNG"}
          </Button>

          {/* Copy Button */}
          <Button
            variant="outline"
            size="sm"
            onClick={handleCopy}
            disabled={isCopying}
            className="gap-2"
            aria-label="Copy image to clipboard"
          >
            {isCopying ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : copySuccess ? (
              <Check className="h-4 w-4 text-green-500" />
            ) : (
              <Copy className="h-4 w-4" />
            )}
            {copySuccess ? "Copied!" : "Copy to Clipboard"}
          </Button>

          {/* Regenerate Button */}
          {onRegenerate && (
            <Button
              variant="secondary"
              size="sm"
              onClick={handleRegenerate}
              disabled={isRegenerating}
              className="gap-2"
              aria-label="Regenerate image with same settings"
            >
              {isRegenerating ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RefreshCw className="h-4 w-4" />
              )}
              {isRegenerating ? "Regenerating..." : "Regenerate"}
            </Button>
          )}
        </div>

        {/* Error Messages */}
        {(downloadError || copyError) && (
          <div className="flex items-start gap-2 text-destructive bg-destructive/10 p-3 rounded-md text-sm">
            <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
            <div>
              {downloadError && <p>Download error: {downloadError}</p>}
              {copyError && <p>Copy error: {copyError}</p>}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
