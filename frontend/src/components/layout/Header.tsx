import { Linkedin, Github, CheckCircle2, Key } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useAppStore } from "@/store/appStore"

export function Header() {
  const { claudeAuth, openaiAuth } = useAppStore()

  // Determine connection status
  const isAnyConnected = claudeAuth.isConnected || openaiAuth.isConnected
  const connectedProviders: string[] = []
  if (claudeAuth.isConnected) connectedProviders.push("Claude")
  if (openaiAuth.isConnected) connectedProviders.push("OpenAI")

  return (
    <header className="border-b">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Linkedin className="h-6 w-6 text-primary" />
          <h1 className="text-xl font-semibold">LinkedIn Content Generator</h1>
        </div>
        <div className="flex items-center gap-4">
          {/* AI Connection Status Indicator */}
          {isAnyConnected ? (
            <Badge className="bg-green-500 hover:bg-green-500 text-white gap-1">
              <CheckCircle2 className="h-3 w-3" />
              {connectedProviders.join(" + ")} Ready
            </Badge>
          ) : (
            <Badge variant="outline" className="gap-1 text-muted-foreground">
              <Key className="h-3 w-3" />
              No AI Connected
            </Badge>
          )}
          <Button variant="ghost" size="icon" asChild>
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="GitHub"
            >
              <Github className="h-5 w-5" />
            </a>
          </Button>
        </div>
      </div>
    </header>
  )
}
