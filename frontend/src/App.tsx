import { useState } from "react"
import { Header } from "@/components/layout/Header"
import { RepoInputForm } from "@/components/repo-input/RepoInputForm"
import { AnalysisCard } from "@/components/analysis/AnalysisCard"
import { PostCard } from "@/components/posts/PostCard"
import { AIPostGenerator } from "@/components/posts/AIPostGenerator"
import { ClaudeConnectionStatus } from "@/components/claude-auth/ClaudeConnectionStatus"
import { OpenAIConnectionStatus } from "@/components/openai-auth/OpenAIConnectionStatus"
import { TermsPage } from "@/components/legal/TermsPage"
import { useAppStore } from "@/store/appStore"

type Page = "home" | "terms"

function App() {
  const { analysis } = useAppStore()
  const [currentPage, setCurrentPage] = useState<Page>("home")

  if (currentPage === "terms") {
    return <TermsPage onBack={() => setCurrentPage("home")} />
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-2">
              Transform GitHub Projects into LinkedIn Posts
            </h2>
            <p className="text-muted-foreground">
              Analyze your repositories and generate engaging content for your professional network
            </p>
          </div>

          {/* AI Provider Connections - Always visible for easy access */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">AI Providers</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <p className="text-sm text-muted-foreground mb-2">Anthropic Claude</p>
                <ClaudeConnectionStatus />
              </div>
              <div>
                <p className="text-sm text-muted-foreground mb-2">OpenAI GPT</p>
                <OpenAIConnectionStatus />
              </div>
            </div>
          </div>

          <RepoInputForm />
          <AnalysisCard />

          {/* Show both post options when analysis is complete */}
          {analysis && (
            <>
              <AIPostGenerator analysis={analysis} />
              <PostCard />
            </>
          )}
        </div>
      </main>
      <footer className="border-t py-6 bg-muted/30">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto space-y-4">
            <div className="text-center text-sm text-muted-foreground">
              Built for developers who want to share their work
            </div>
            <div className="text-center text-xs text-muted-foreground space-y-2">
              <p className="font-medium">Privacy Notice</p>
              <p>
                Your API keys are encrypted (AES-256) and stored temporarily on our servers for session use only.
                Keys are automatically deleted after 24 hours of inactivity.
              </p>
              <p>
                <strong>Cross-border Transfer:</strong> When you use this service, your API keys are transmitted to
                Anthropic (USA) or OpenAI (USA) to process your requests. By connecting your API key, you consent
                to this data transfer.
              </p>
              <p className="text-muted-foreground/70">
                We do not store, log, or have access to your generated content. All processing happens via your own API keys.
              </p>
            </div>
            <div className="text-center pt-2 border-t border-border/50">
              <button
                onClick={() => setCurrentPage("terms")}
                className="text-xs text-muted-foreground hover:text-foreground underline-offset-4 hover:underline transition-colors"
              >
                Terms & Conditions
              </button>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default App
