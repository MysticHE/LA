import { Header } from "@/components/layout/Header"
import { RepoInputForm } from "@/components/repo-input/RepoInputForm"
import { AnalysisCard } from "@/components/analysis/AnalysisCard"
import { PostCard } from "@/components/posts/PostCard"
import { AIPostGenerator } from "@/components/posts/AIPostGenerator"
import { ClaudeConnectionStatus } from "@/components/claude-auth/ClaudeConnectionStatus"
import { useAppStore } from "@/store/appStore"

function App() {
  const { analysis } = useAppStore()

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

          {/* Claude Connection - Always visible for easy access */}
          <ClaudeConnectionStatus />

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
      <footer className="border-t py-4">
        <div className="container mx-auto px-4 text-center text-sm text-muted-foreground">
          Built for developers who want to share their work
        </div>
      </footer>
    </div>
  )
}

export default App
