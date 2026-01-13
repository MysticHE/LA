import { useState } from "react"
import { CheckCircle2, Unplug, Key, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { useAppStore } from "@/store/appStore"
import { api } from "@/lib/api"
import { OpenAIAuthForm } from "./OpenAIAuthForm"

interface OpenAIConnectionStatusProps {
  sessionId?: string
}

export function OpenAIConnectionStatus({
  sessionId = "default",
}: OpenAIConnectionStatusProps) {
  const {
    openaiAuth,
    disconnectOpenAI,
    setOpenAILoading,
    setOpenAIError,
  } = useAppStore()

  const [showConfirmation, setShowConfirmation] = useState(false)

  const handleDisconnectClick = () => {
    setShowConfirmation(true)
  }

  const handleCancelDisconnect = () => {
    setShowConfirmation(false)
  }

  const handleConfirmDisconnect = async () => {
    setOpenAILoading(true)
    setOpenAIError(null)

    try {
      const response = await api.disconnectOpenAI(sessionId)

      if (!response.connected) {
        disconnectOpenAI()
      } else {
        setOpenAIError("Failed to disconnect. Please try again.")
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : "Network error. Please try again."
      setOpenAIError(errorMessage)
    } finally {
      setOpenAILoading(false)
      setShowConfirmation(false)
    }
  }

  // Disconnected state - show the connect form
  if (!openaiAuth.isConnected) {
    return <OpenAIAuthForm />
  }

  // Connected state
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Badge className="bg-green-500 hover:bg-green-500 text-white gap-1">
              <CheckCircle2 className="h-3 w-3" />
              Connected
            </Badge>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Key className="h-4 w-4" />
              <span>API Key: {openaiAuth.maskedKey}</span>
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
                disabled={openaiAuth.isLoading}
              >
                {openaiAuth.isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  "Yes"
                )}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleCancelDisconnect}
                disabled={openaiAuth.isLoading}
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

        {openaiAuth.error && (
          <div className="mt-4 text-sm text-destructive">
            {openaiAuth.error}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
