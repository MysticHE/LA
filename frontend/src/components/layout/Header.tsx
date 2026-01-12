import { Linkedin, Github, CheckCircle2, Key } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useAppStore } from "@/store/appStore"

export function Header() {
  const { claudeAuth } = useAppStore()

  return (
    <header className="border-b">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Linkedin className="h-6 w-6 text-primary" />
          <h1 className="text-xl font-semibold">LinkedIn Content Generator</h1>
        </div>
        <div className="flex items-center gap-4">
          {/* Claude Connection Status Indicator */}
          {claudeAuth.isConnected ? (
            <Badge className="bg-green-500 hover:bg-green-500 text-white gap-1">
              <CheckCircle2 className="h-3 w-3" />
              Claude Connected
            </Badge>
          ) : (
            <Badge variant="outline" className="gap-1 text-muted-foreground">
              <Key className="h-3 w-3" />
              Claude Not Connected
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
