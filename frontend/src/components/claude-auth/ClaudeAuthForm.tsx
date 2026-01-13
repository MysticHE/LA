import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Key, Loader2, CheckCircle2, AlertCircle, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { useAppStore } from "@/store/appStore"
import { api, ApiError, getUserFriendlyError } from "@/lib/api"

const formSchema = z.object({
  apiKey: z
    .string()
    .min(1, "API key is required")
    .regex(/^sk-ant-/, "API key must start with 'sk-ant-'"),
  consent: z.boolean().refine((val) => val === true, {
    message: "You must consent to the data transfer to continue",
  }),
})

type FormData = z.infer<typeof formSchema>

interface ClaudeAuthFormProps {
  onSuccess?: () => void
}

export function ClaudeAuthForm({ onSuccess }: ClaudeAuthFormProps) {
  const {
    claudeAuth,
    setClaudeConnected,
    setClaudeLoading,
    setClaudeError
  } = useAppStore()

  const [showSuccess, setShowSuccess] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    watch,
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      apiKey: "",
      consent: false,
    },
  })

  const consentChecked = watch("consent")

  const onSubmit = async (data: FormData) => {
    setClaudeLoading(true)
    setClaudeError(null)
    setShowSuccess(false)

    try {
      const response = await api.connectClaude(data.apiKey)

      if (response.connected) {
        setClaudeConnected(true, response.masked_key)
        setShowSuccess(true)
        reset()
        onSuccess?.()
      } else {
        setClaudeError(response.error || "Failed to connect. Please check your API key.")
      }
    } catch (error) {
      // Use ApiError message directly (already user-friendly from fetchWithTimeout)
      // or map generic errors to friendly messages
      if (error instanceof ApiError) {
        setClaudeError(error.message)
      } else if (error instanceof Error) {
        setClaudeError(getUserFriendlyError(error.message))
      } else {
        setClaudeError("Something went wrong. Please try again.")
      }
    } finally {
      setClaudeLoading(false)
    }
  }

  const handleRetry = () => {
    setClaudeError(null)
    setShowSuccess(false)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Key className="h-5 w-5" />
          Connect Claude API
        </CardTitle>
        <CardDescription>
          Enter your Anthropic API key to enable AI-powered content generation
        </CardDescription>
      </CardHeader>
      <CardContent>
        {showSuccess ? (
          <div className="flex items-center gap-2 text-green-600 bg-green-50 p-3 rounded-md">
            <CheckCircle2 className="h-5 w-5" />
            <span>Successfully connected to Claude!</span>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Input
                type="password"
                placeholder="sk-ant-..."
                {...register("apiKey")}
                disabled={claudeAuth.isLoading}
                aria-label="Claude API Key"
              />
              {errors.apiKey && (
                <p className="text-sm text-destructive">
                  {errors.apiKey.message}
                </p>
              )}
            </div>

            {claudeAuth.error && (
              <div className="flex items-start gap-2 text-destructive bg-destructive/10 p-3 rounded-md">
                <AlertCircle className="h-5 w-5 mt-0.5 shrink-0" />
                <div className="flex-1">
                  <p className="text-sm">{claudeAuth.error}</p>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="mt-2 h-8 px-2"
                    onClick={handleRetry}
                  >
                    <RefreshCw className="h-4 w-4 mr-1" />
                    Try Again
                  </Button>
                </div>
              </div>
            )}

            <div className="space-y-2">
              <Checkbox
                {...register("consent")}
                label="I consent to my API key being transmitted to Anthropic (USA) for processing requests. My key will be encrypted and automatically deleted after 24 hours of inactivity."
              />
              {errors.consent && (
                <p className="text-sm text-destructive">
                  {errors.consent.message}
                </p>
              )}
            </div>

            <Button
              type="submit"
              disabled={claudeAuth.isLoading || !consentChecked}
              className="w-full"
            >
              {claudeAuth.isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Connecting...
                </>
              ) : (
                <>
                  <Key className="h-4 w-4" />
                  Connect
                </>
              )}
            </Button>

            <p className="text-xs text-muted-foreground">
              Your API key is encrypted and stored securely. Get your key from{" "}
              <a
                href="https://console.anthropic.com/settings/keys"
                target="_blank"
                rel="noopener noreferrer"
                className="text-primary hover:underline"
              >
                Anthropic Console
              </a>
            </p>
          </form>
        )}
      </CardContent>
    </Card>
  )
}
