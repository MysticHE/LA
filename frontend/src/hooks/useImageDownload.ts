import { useState, useCallback } from "react"

interface DownloadOptions {
  filename?: string
}

interface UseImageDownloadReturn {
  download: (imageBase64: string, options?: DownloadOptions) => Promise<boolean>
  copyToClipboard: (imageBase64: string) => Promise<boolean>
  isDownloading: boolean
  isCopying: boolean
  downloadError: string | null
  copyError: string | null
}

/**
 * Hook for downloading and copying images
 * Handles base64 image data for download as PNG and clipboard copy
 */
export function useImageDownload(): UseImageDownloadReturn {
  const [isDownloading, setIsDownloading] = useState(false)
  const [isCopying, setIsCopying] = useState(false)
  const [downloadError, setDownloadError] = useState<string | null>(null)
  const [copyError, setCopyError] = useState<string | null>(null)

  /**
   * Download base64 image as PNG file
   */
  const download = useCallback(
    async (imageBase64: string, options?: DownloadOptions): Promise<boolean> => {
      setIsDownloading(true)
      setDownloadError(null)

      try {
        // Create blob from base64
        const byteCharacters = atob(imageBase64)
        const byteNumbers = new Array(byteCharacters.length)
        for (let i = 0; i < byteCharacters.length; i++) {
          byteNumbers[i] = byteCharacters.charCodeAt(i)
        }
        const byteArray = new Uint8Array(byteNumbers)
        const blob = new Blob([byteArray], { type: "image/png" })

        // Create download link
        const url = URL.createObjectURL(blob)
        const link = document.createElement("a")
        link.href = url
        link.download = options?.filename || `linkedin-image-${Date.now()}.png`

        // Trigger download
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)

        // Cleanup
        URL.revokeObjectURL(url)

        return true
      } catch (error) {
        const message = error instanceof Error ? error.message : "Failed to download image"
        setDownloadError(message)
        console.error("Download error:", error)
        return false
      } finally {
        setIsDownloading(false)
      }
    },
    []
  )

  /**
   * Copy base64 image to clipboard
   * Uses the Clipboard API with blob data
   */
  const copyToClipboard = useCallback(async (imageBase64: string): Promise<boolean> => {
    setIsCopying(true)
    setCopyError(null)

    try {
      // Check if clipboard API is available
      if (!navigator.clipboard || !window.ClipboardItem) {
        throw new Error("Clipboard API not supported in this browser")
      }

      // Create blob from base64
      const byteCharacters = atob(imageBase64)
      const byteNumbers = new Array(byteCharacters.length)
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i)
      }
      const byteArray = new Uint8Array(byteNumbers)
      const blob = new Blob([byteArray], { type: "image/png" })

      // Copy to clipboard
      const clipboardItem = new ClipboardItem({ "image/png": blob })
      await navigator.clipboard.write([clipboardItem])

      return true
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to copy image to clipboard"
      setCopyError(message)
      console.error("Clipboard error:", error)
      return false
    } finally {
      setIsCopying(false)
    }
  }, [])

  return {
    download,
    copyToClipboard,
    isDownloading,
    isCopying,
    downloadError,
    copyError,
  }
}
