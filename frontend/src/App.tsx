import { useState } from "react"
import { Header } from "@/components/layout/Header"
import { RepoInputForm } from "@/components/repo-input/RepoInputForm"
import { AnalysisCard } from "@/components/analysis/AnalysisCard"
import { PostCard } from "@/components/posts/PostCard"
import { AIPostGenerator } from "@/components/posts/AIPostGenerator"
import { AIProvidersPanel } from "@/components/providers/AIProvidersPanel"
import { TermsModal } from "@/components/legal/TermsModal"
import { PrivacyModal } from "@/components/legal/PrivacyModal"
import { useAppStore } from "@/store/appStore"

function App() {
  const { analysis } = useAppStore()
  const [termsOpen, setTermsOpen] = useState(false)
  const [privacyOpen, setPrivacyOpen] = useState(false)

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

          {/* AI Provider Connections */}
          <AIProvidersPanel />

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
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center justify-center gap-4 text-xs">
              <button
                onClick={() => setPrivacyOpen(true)}
                className="text-muted-foreground hover:text-foreground underline-offset-4 hover:underline transition-colors"
              >
                Privacy Notice
              </button>
              <span className="text-muted-foreground/50">|</span>
              <button
                onClick={() => setTermsOpen(true)}
                className="text-muted-foreground hover:text-foreground underline-offset-4 hover:underline transition-colors"
              >
                Terms & Conditions
              </button>
            </div>
          </div>
        </div>
      </footer>

      {/* Modals */}
      <TermsModal open={termsOpen} onOpenChange={setTermsOpen} />
      <PrivacyModal open={privacyOpen} onOpenChange={setPrivacyOpen} />
    </div>
  )
}

export default App
