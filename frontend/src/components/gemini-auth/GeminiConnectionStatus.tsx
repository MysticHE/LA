import { useState } from "react"
import { CheckCircle2, Unplug, Key, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { useAppStore } from "@/store/appStore"
import { api } from "@/lib/api"
import { GeminiAuthForm } from "./GeminiAuthForm"

export function GeminiConnectionStatus() {
  const {
    geminiAuth,
    disconnectGemini,
    setGeminiLoading,
    setGeminiError,
  } = useAppStore()

  const [showConfirmation, setShowConfirmation] = useState(false)

  const handleDisconnectClick = () => {
    setShowConfirmation(true)
  }

  const handleCancelDisconnect = () => {
    setShowConfirmation(false)
  }

  const handleConfirmDisconnect = async () => {
    setGeminiLoading(true)
    setGeminiError(null)

    try {
      const response = await api.disconnectGemini()

      if (!response.connected) {
        disconnectGemini()
      } else {
        setGeminiError("Failed to disconnect. Please try again.")
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : "Network error. Please try again."
      setGeminiError(errorMessage)
    } finally {
      setGeminiLoading(false)
      setShowConfirmation(false)
    }
  }

  // Disconnected state - show the connect form
  if (!geminiAuth.isConnected) {
    return <GeminiAuthForm />
  }

  // Format masked key to show only last 4 chars with limited asterisks
  const formatMaskedKey = (key: string | null) => {
    if (!key) return "****"
    // Show "AIza...xxxx" format for cleaner display
    const last4 = key.slice(-4)
    return `AIza...${last4}`
  }

  // Connected state
  return (
    <Card>
      <CardContent className="pt-6 pb-6">
        <div className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Badge className="bg-green-500 hover:bg-green-500 text-white gap-1">
                <CheckCircle2 className="h-3 w-3" />
                Connected
              </Badge>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Key className="h-4 w-4 shrink-0" />
                <span className="font-mono">{formatMaskedKey(geminiAuth.maskedKey)}</span>
              </div>
            </div>

            {showConfirmation ? (
              <div className="flex items-center gap-2">
                <span className="text-sm text-muted-foreground">
                  Disconnect?
                </span>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleConfirmDisconnect}
                  disabled={geminiAuth.isLoading}
                >
                  {geminiAuth.isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    "Yes"
                  )}
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCancelDisconnect}
                  disabled={geminiAuth.isLoading}
                >
                  No
                </Button>
              </div>
            ) : (
              <Button
                variant="ghost"
                size="sm"
                onClick={handleDisconnectClick}
                className="text-muted-foreground hover:text-destructive"
              >
                <Unplug className="h-4 w-4 mr-1" />
                Disconnect
              </Button>
            )}
          </div>

          <p className="text-xs text-muted-foreground">
            Your Gemini API key is connected and ready to generate images.
          </p>
        </div>

        {geminiAuth.error && (
          <div className="mt-4 text-sm text-destructive">
            {geminiAuth.error}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
