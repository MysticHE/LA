import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { motion, AnimatePresence } from "framer-motion"
import {
  Key,
  Loader2,
  CheckCircle2,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  Unplug,
  Sparkles,
  ImageIcon,
  ExternalLink,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { useAppStore } from "@/store/appStore"
import { api, ApiError, getUserFriendlyError } from "@/lib/api"

const claudeSchema = z.object({
  apiKey: z
    .string()
    .min(1, "API key is required")
    .regex(/^sk-ant-/, "Must start with 'sk-ant-'"),
})

const openaiSchema = z.object({
  apiKey: z
    .string()
    .min(1, "API key is required")
    .regex(/^sk-/, "Must start with 'sk-'"),
})

const geminiSchema = z.object({
  apiKey: z
    .string()
    .min(1, "API key is required")
    .regex(/^AIza/, "Must start with 'AIza'"),
})

type ClaudeFormData = z.infer<typeof claudeSchema>
type OpenAIFormData = z.infer<typeof openaiSchema>
type GeminiFormData = z.infer<typeof geminiSchema>

const PROVIDERS = {
  claude: {
    name: "Claude",
    company: "Anthropic",
    placeholder: "sk-ant-...",
    url: "https://console.anthropic.com/settings/keys",
    urlLabel: "Anthropic Console",
  },
  openai: {
    name: "GPT",
    company: "OpenAI",
    placeholder: "sk-...",
    url: "https://platform.openai.com/api-keys",
    urlLabel: "OpenAI Platform",
  },
  gemini: {
    name: "Gemini",
    company: "Google",
    placeholder: "AIza...",
    url: "https://aistudio.google.com/app/apikey",
    urlLabel: "Google AI Studio",
  },
} as const

export function AIProvidersPanel() {
  const {
    claudeAuth,
    openaiAuth,
    geminiAuth,
    setClaudeConnected,
    setClaudeLoading,
    setClaudeError,
    disconnectClaude,
    setOpenAIConnected,
    setOpenAILoading,
    setOpenAIError,
    disconnectOpenAI,
    setGeminiConnected,
    setGeminiLoading,
    setGeminiError,
    disconnectGemini,
  } = useAppStore()

  const [consent, setConsent] = useState(false)
  const [imageGenExpanded, setImageGenExpanded] = useState(false)
  const [activeTab, setActiveTab] = useState<"claude" | "openai">("claude")
  const [disconnectConfirm, setDisconnectConfirm] = useState<string | null>(null)

  const claudeForm = useForm<ClaudeFormData>({
    resolver: zodResolver(claudeSchema),
    defaultValues: { apiKey: "" },
  })

  const openaiForm = useForm<OpenAIFormData>({
    resolver: zodResolver(openaiSchema),
    defaultValues: { apiKey: "" },
  })

  const geminiForm = useForm<GeminiFormData>({
    resolver: zodResolver(geminiSchema),
    defaultValues: { apiKey: "" },
  })

  const handleClaudeSubmit = async (data: ClaudeFormData) => {
    if (!consent) return
    setClaudeLoading(true)
    setClaudeError(null)
    try {
      const response = await api.connectClaude(data.apiKey)
      if (response.connected) {
        setClaudeConnected(true, response.masked_key)
        claudeForm.reset()
      } else {
        setClaudeError(response.error || "Failed to connect")
      }
    } catch (error) {
      if (error instanceof ApiError) {
        setClaudeError(error.message)
      } else if (error instanceof Error) {
        setClaudeError(getUserFriendlyError(error.message))
      } else {
        setClaudeError("Something went wrong")
      }
    } finally {
      setClaudeLoading(false)
    }
  }

  const handleOpenAISubmit = async (data: OpenAIFormData) => {
    if (!consent) return
    setOpenAILoading(true)
    setOpenAIError(null)
    try {
      const response = await api.connectOpenAI(data.apiKey)
      if (response.connected) {
        setOpenAIConnected(true, response.masked_key)
        openaiForm.reset()
      } else {
        setOpenAIError(response.error || "Failed to connect")
      }
    } catch (error) {
      if (error instanceof ApiError) {
        setOpenAIError(error.message)
      } else if (error instanceof Error) {
        setOpenAIError(getUserFriendlyError(error.message))
      } else {
        setOpenAIError("Something went wrong")
      }
    } finally {
      setOpenAILoading(false)
    }
  }

  const handleGeminiSubmit = async (data: GeminiFormData) => {
    if (!consent) return
    setGeminiLoading(true)
    setGeminiError(null)
    try {
      const response = await api.connectGemini(data.apiKey)
      if (response.connected) {
        setGeminiConnected(true, response.masked_key)
        geminiForm.reset()
      } else {
        setGeminiError(response.error || "Failed to connect")
      }
    } catch (error) {
      if (error instanceof ApiError) {
        setGeminiError(error.message)
      } else if (error instanceof Error) {
        setGeminiError(getUserFriendlyError(error.message))
      } else {
        setGeminiError("Something went wrong")
      }
    } finally {
      setGeminiLoading(false)
    }
  }

  const handleDisconnect = async (provider: "claude" | "openai" | "gemini") => {
    const setLoading = {
      claude: setClaudeLoading,
      openai: setOpenAILoading,
      gemini: setGeminiLoading,
    }[provider]
    const setError = {
      claude: setClaudeError,
      openai: setOpenAIError,
      gemini: setGeminiError,
    }[provider]
    const disconnect = {
      claude: disconnectClaude,
      openai: disconnectOpenAI,
      gemini: disconnectGemini,
    }[provider]
    const apiCall = {
      claude: api.disconnectClaude,
      openai: api.disconnectOpenAI,
      gemini: api.disconnectGemini,
    }[provider]

    setLoading(true)
    setError(null)
    try {
      const response = await apiCall()
      if (!response.connected) {
        disconnect()
      }
    } catch {
      setError("Failed to disconnect")
    } finally {
      setLoading(false)
      setDisconnectConfirm(null)
    }
  }

  const formatMaskedKey = (key: string | null, prefix: string) => {
    if (!key) return "****"
    const last4 = key.slice(-4)
    return `${prefix}...${last4}`
  }

  const hasTextProvider = claudeAuth.isConnected || openaiAuth.isConnected

  return (
    <Card>
      <CardHeader className="pb-4">
        <CardTitle className="text-lg flex items-center gap-2">
          <Key className="h-5 w-5" />
          API Connections
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Text Generation Section */}
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-primary" />
            <span className="text-sm font-medium">Content Generation</span>
            <Badge variant="secondary" className="text-xs">
              Connect one
            </Badge>
            {hasTextProvider && (
              <Badge className="bg-green-500 hover:bg-green-500 text-white text-xs ml-auto">
                <CheckCircle2 className="h-3 w-3 mr-1" />
                Ready
              </Badge>
            )}
          </div>

          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as "claude" | "openai")}>
            <TabsList className="w-full grid grid-cols-2">
              <TabsTrigger value="claude" className="gap-2">
                Claude
                {claudeAuth.isConnected && (
                  <CheckCircle2 className="h-3 w-3 text-green-500" />
                )}
              </TabsTrigger>
              <TabsTrigger value="openai" className="gap-2">
                GPT
                {openaiAuth.isConnected && (
                  <CheckCircle2 className="h-3 w-3 text-green-500" />
                )}
              </TabsTrigger>
            </TabsList>

            <TabsContent value="claude" className="mt-3">
              {claudeAuth.isConnected ? (
                <ConnectedState
                  provider="claude"
                  maskedKey={formatMaskedKey(claudeAuth.maskedKey, "sk-ant-")}
                  isLoading={claudeAuth.isLoading}
                  showConfirm={disconnectConfirm === "claude"}
                  onDisconnectClick={() => setDisconnectConfirm("claude")}
                  onConfirm={() => handleDisconnect("claude")}
                  onCancel={() => setDisconnectConfirm(null)}
                  error={claudeAuth.error}
                />
              ) : (
                <ProviderForm
                  provider="claude"
                  form={claudeForm}
                  onSubmit={handleClaudeSubmit}
                  isLoading={claudeAuth.isLoading}
                  error={claudeAuth.error}
                  consent={consent}
                  onErrorClear={() => setClaudeError(null)}
                />
              )}
            </TabsContent>

            <TabsContent value="openai" className="mt-3">
              {openaiAuth.isConnected ? (
                <ConnectedState
                  provider="openai"
                  maskedKey={formatMaskedKey(openaiAuth.maskedKey, "sk-")}
                  isLoading={openaiAuth.isLoading}
                  showConfirm={disconnectConfirm === "openai"}
                  onDisconnectClick={() => setDisconnectConfirm("openai")}
                  onConfirm={() => handleDisconnect("openai")}
                  onCancel={() => setDisconnectConfirm(null)}
                  error={openaiAuth.error}
                />
              ) : (
                <ProviderForm
                  provider="openai"
                  form={openaiForm}
                  onSubmit={handleOpenAISubmit}
                  isLoading={openaiAuth.isLoading}
                  error={openaiAuth.error}
                  consent={consent}
                  onErrorClear={() => setOpenAIError(null)}
                />
              )}
            </TabsContent>
          </Tabs>
        </div>

        {/* Divider */}
        <div className="border-t" />

        {/* Image Generation Section */}
        <div className="space-y-3">
          <button
            type="button"
            onClick={() => setImageGenExpanded(!imageGenExpanded)}
            className="w-full flex items-center justify-between text-left cursor-pointer hover:opacity-80 transition-opacity"
          >
            <div className="flex items-center gap-2">
              <ImageIcon className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Image Generation</span>
              <Badge variant="outline" className="text-xs">
                Optional
              </Badge>
              {geminiAuth.isConnected && (
                <Badge className="bg-green-500 hover:bg-green-500 text-white text-xs">
                  <CheckCircle2 className="h-3 w-3 mr-1" />
                  Connected
                </Badge>
              )}
            </div>
            {imageGenExpanded ? (
              <ChevronUp className="h-4 w-4 text-muted-foreground" />
            ) : (
              <ChevronDown className="h-4 w-4 text-muted-foreground" />
            )}
          </button>

          <AnimatePresence>
            {imageGenExpanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3, ease: "easeInOut" }}
              className="pt-2 overflow-hidden"
            >
              {geminiAuth.isConnected ? (
                <ConnectedState
                  provider="gemini"
                  maskedKey={formatMaskedKey(geminiAuth.maskedKey, "AIza")}
                  isLoading={geminiAuth.isLoading}
                  showConfirm={disconnectConfirm === "gemini"}
                  onDisconnectClick={() => setDisconnectConfirm("gemini")}
                  onConfirm={() => handleDisconnect("gemini")}
                  onCancel={() => setDisconnectConfirm(null)}
                  error={geminiAuth.error}
                />
              ) : (
                <ProviderForm
                  provider="gemini"
                  form={geminiForm}
                  onSubmit={handleGeminiSubmit}
                  isLoading={geminiAuth.isLoading}
                  error={geminiAuth.error}
                  consent={consent}
                  onErrorClear={() => setGeminiError(null)}
                />
              )}
            </motion.div>
          )}
          </AnimatePresence>
        </div>

        {/* Divider */}
        <div className="border-t" />

        {/* Global Consent */}
        <div className="space-y-3">
          <Checkbox
            checked={consent}
            onChange={(e) => setConsent(e.target.checked)}
            label={
              <span className="text-xs text-muted-foreground">
                I agree to the Terms & Conditions for API key usage
              </span>
            }
          />
          <p className="text-xs text-muted-foreground">
            API keys are encrypted during your session.
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

interface ConnectedStateProps {
  provider: "claude" | "openai" | "gemini"
  maskedKey: string
  isLoading: boolean
  showConfirm: boolean
  onDisconnectClick: () => void
  onConfirm: () => void
  onCancel: () => void
  error: string | null
}

function ConnectedState({
  provider,
  maskedKey,
  isLoading,
  showConfirm,
  onDisconnectClick,
  onConfirm,
  onCancel,
  error,
}: ConnectedStateProps) {
  const info = PROVIDERS[provider]

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-sm">
            <Key className="h-4 w-4 text-muted-foreground" />
            <span className="font-mono text-xs">{maskedKey}</span>
          </div>
        </div>
        {showConfirm ? (
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Disconnect?</span>
            <Button variant="destructive" size="sm" onClick={onConfirm} disabled={isLoading}>
              {isLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : "Yes"}
            </Button>
            <Button variant="outline" size="sm" onClick={onCancel} disabled={isLoading}>
              No
            </Button>
          </div>
        ) : (
          <Button
            variant="ghost"
            size="sm"
            onClick={onDisconnectClick}
            className="text-muted-foreground hover:text-destructive h-8"
          >
            <Unplug className="h-3 w-3 mr-1" />
            Disconnect
          </Button>
        )}
      </div>
      {error && (
        <p className="text-xs text-destructive flex items-center gap-1">
          <AlertCircle className="h-3 w-3" />
          {error}
        </p>
      )}
      <p className="text-xs text-muted-foreground">
        Connected to {info.company} {info.name}
      </p>
    </div>
  )
}

interface ProviderFormProps {
  provider: "claude" | "openai" | "gemini"
  form: ReturnType<typeof useForm<ClaudeFormData | OpenAIFormData | GeminiFormData>>
  onSubmit: (data: ClaudeFormData | OpenAIFormData | GeminiFormData) => void
  isLoading: boolean
  error: string | null
  consent: boolean
  onErrorClear: () => void
}

function ProviderForm({
  provider,
  form,
  onSubmit,
  isLoading,
  error,
  consent,
  onErrorClear,
}: ProviderFormProps) {
  const info = PROVIDERS[provider]
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = form

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
      <div className="flex gap-2">
        <div className="flex-1">
          <Input
            type="password"
            placeholder={info.placeholder}
            {...register("apiKey")}
            disabled={isLoading}
            aria-label={`${info.company} API Key`}
            className="h-9"
          />
        </div>
        <Button
          type="submit"
          disabled={isLoading || !consent}
          size="sm"
          className="h-9 px-4"
        >
          {isLoading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            "Connect"
          )}
        </Button>
      </div>

      {errors.apiKey && (
        <p className="text-xs text-destructive">{errors.apiKey.message}</p>
      )}

      {error && (
        <div className="flex items-start gap-2 text-destructive bg-destructive/10 p-2 rounded text-xs">
          <AlertCircle className="h-3 w-3 mt-0.5 shrink-0" />
          <span className="flex-1">{error}</span>
          <button
            type="button"
            onClick={onErrorClear}
            className="text-xs underline hover:no-underline"
          >
            Dismiss
          </button>
        </div>
      )}

      <p className="text-xs text-muted-foreground flex items-center gap-1">
        Get your key from{" "}
        <a
          href={info.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary hover:underline inline-flex items-center gap-0.5"
        >
          {info.urlLabel}
          <ExternalLink className="h-3 w-3" />
        </a>
      </p>
    </form>
  )
}
