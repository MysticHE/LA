import { useEffect } from "react"
import { Bot, Sparkles } from "lucide-react"
import { useAppStore } from "@/store/appStore"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
} from "@/components/ui/card"

type AIProvider = "claude" | "openai"

interface ProviderOption {
  id: AIProvider
  label: string
  icon: typeof Bot
}

const PROVIDERS: ProviderOption[] = [
  { id: "claude", label: "Claude", icon: Sparkles },
  { id: "openai", label: "OpenAI", icon: Bot },
]

interface ProviderSelectorProps {
  className?: string
}

export function ProviderSelector({ className }: ProviderSelectorProps) {
  const {
    claudeAuth,
    openaiAuth,
    selectedProvider,
    setSelectedProvider,
  } = useAppStore()

  const claudeConnected = claudeAuth.isConnected
  const openaiConnected = openaiAuth.isConnected

  // Auto-select provider based on connection status
  useEffect(() => {
    // If both connected, keep current selection or default to claude
    if (claudeConnected && openaiConnected) {
      if (!selectedProvider) {
        setSelectedProvider("claude")
      }
      return
    }

    // If only one connected, auto-select it
    if (claudeConnected && !openaiConnected) {
      setSelectedProvider("claude")
      return
    }

    if (openaiConnected && !claudeConnected) {
      setSelectedProvider("openai")
      return
    }

    // Neither connected, clear selection
    setSelectedProvider(null)
  }, [claudeConnected, openaiConnected, selectedProvider, setSelectedProvider])

  // Get connected providers
  const connectedProviders = PROVIDERS.filter((provider) => {
    if (provider.id === "claude") return claudeConnected
    if (provider.id === "openai") return openaiConnected
    return false
  })

  // If no providers connected, don't render
  if (connectedProviders.length === 0) {
    return null
  }

  // If only one provider, show simple display (no dropdown needed)
  if (connectedProviders.length === 1) {
    const provider = connectedProviders[0]
    const Icon = provider.icon
    return (
      <div className={className}>
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Icon className="h-4 w-4" />
          <span>Using {provider.label}</span>
        </div>
      </div>
    )
  }

  // Both providers connected - show selector
  const handleProviderSelect = (providerId: AIProvider) => {
    setSelectedProvider(providerId)
  }

  return (
    <Card className={className}>
      <CardContent className="py-3 px-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">AI Provider</span>
          <div className="flex gap-2">
            {PROVIDERS.map((provider) => {
              const isConnected = provider.id === "claude" ? claudeConnected : openaiConnected
              if (!isConnected) return null

              const Icon = provider.icon
              const isSelected = selectedProvider === provider.id

              return (
                <Button
                  key={provider.id}
                  variant={isSelected ? "default" : "outline"}
                  size="sm"
                  onClick={() => handleProviderSelect(provider.id)}
                  className="gap-1"
                  aria-label={`Select ${provider.label} as AI provider`}
                  aria-pressed={isSelected}
                >
                  <Icon className="h-4 w-4" />
                  {provider.label}
                </Button>
              )
            })}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
