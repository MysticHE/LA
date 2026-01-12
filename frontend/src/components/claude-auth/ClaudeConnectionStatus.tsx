import { useState } from "react"
import { CheckCircle2, Unplug, Key, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { useAppStore } from "@/store/appStore"
import { api } from "@/lib/api"
import { ClaudeAuthForm } from "./ClaudeAuthForm"

interface ClaudeConnectionStatusProps {
  sessionId?: string
}

export function ClaudeConnectionStatus({
  sessionId = "default",
}: ClaudeConnectionStatusProps) {
  const {
    claudeAuth,
    disconnectClaude,
    setClaudeLoading,
    setClaudeError,
  } = useAppStore()

  const [showConfirmation, setShowConfirmation] = useState(false)

  const handleDisconnectClick = () => {
    setShowConfirmation(true)
  }

  const handleCancelDisconnect = () => {
    setShowConfirmation(false)
  }

  const handleConfirmDisconnect = async () => {
    setClaudeLoading(true)
    setClaudeError(null)

    try {
      const response = await api.disconnectClaude(sessionId)

      if (!response.connected) {
        disconnectClaude()
      } else {
        setClaudeError("Failed to disconnect. Please try again.")
      }
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : "Network error. Please try again."
      setClaudeError(errorMessage)
    } finally {
      setClaudeLoading(false)
      setShowConfirmation(false)
    }
  }

  // Disconnected state - show the connect form
  if (!claudeAuth.isConnected) {
    return <ClaudeAuthForm />
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
              <span>API Key: {claudeAuth.maskedKey}</span>
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
                disabled={claudeAuth.isLoading}
              >
                {claudeAuth.isLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  "Yes"
                )}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleCancelDisconnect}
                disabled={claudeAuth.isLoading}
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

        {claudeAuth.error && (
          <div className="mt-4 text-sm text-destructive">
            {claudeAuth.error}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
