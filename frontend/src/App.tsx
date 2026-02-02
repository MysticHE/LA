import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Github, RefreshCw } from "lucide-react"
import { Header } from "@/components/layout/Header"
import { RepoInputForm } from "@/components/repo-input/RepoInputForm"
import { AnalysisCard } from "@/components/analysis/AnalysisCard"
import { PostCard } from "@/components/posts/PostCard"
import { AIPostGenerator } from "@/components/posts/AIPostGenerator"
import { AIProvidersPanel } from "@/components/providers/AIProvidersPanel"
import { TermsModal } from "@/components/legal/TermsModal"
import { PrivacyModal } from "@/components/legal/PrivacyModal"
import { LinkedInInputForm, RepurposeOptions, ContentPreview } from "@/components/linkedin-input"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { useAppStore } from "@/store/appStore"

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.15, delayChildren: 0.2 }
  }
}

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: "easeOut" as const }
  }
}

function App() {
  const { analysis, inputMode, setInputMode, linkedin } = useAppStore()
  const [termsOpen, setTermsOpen] = useState(false)
  const [privacyOpen, setPrivacyOpen] = useState(false)

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1 container mx-auto px-4 py-8">
        <motion.div
          className="max-w-4xl mx-auto space-y-6"
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          <motion.div variants={itemVariants} className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-2 bg-gradient-to-r from-foreground via-foreground to-foreground/60 bg-clip-text">
              {inputMode === "github"
                ? "Transform GitHub Projects into LinkedIn Posts"
                : "Repurpose LinkedIn Content"}
            </h2>
            <p className="text-muted-foreground">
              {inputMode === "github"
                ? "Analyze your repositories and generate engaging content for your professional network"
                : "Paste any LinkedIn post and create a fresh version with your style"}
            </p>
          </motion.div>

          <motion.div variants={itemVariants}>
            <AIProvidersPanel />
          </motion.div>

          <motion.div variants={itemVariants}>
            <Tabs
              value={inputMode}
              onValueChange={(v) => setInputMode(v as "github" | "linkedin")}
              className="w-full"
            >
              <TabsList className="grid w-full grid-cols-2 mb-4">
                <TabsTrigger value="github" className="gap-2">
                  <Github className="h-4 w-4" />
                  GitHub Repo
                </TabsTrigger>
                <TabsTrigger value="linkedin" className="gap-2">
                  <RefreshCw className="h-4 w-4" />
                  Repurpose Post
                </TabsTrigger>
              </TabsList>

              <TabsContent value="github" className="space-y-6">
                <RepoInputForm />
                <AnalysisCard />
                <AnimatePresence mode="wait">
                  {analysis && (
                    <motion.div
                      key="post-generators"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      transition={{ duration: 0.4 }}
                      className="space-y-6"
                    >
                      <AIPostGenerator analysis={analysis} />
                      <PostCard />
                    </motion.div>
                  )}
                </AnimatePresence>
              </TabsContent>

              <TabsContent value="linkedin" className="space-y-6">
                <LinkedInInputForm />
                <AnimatePresence mode="wait">
                  {linkedin.contentAnalysis && (
                    <motion.div
                      key="repurpose-options"
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -20 }}
                      transition={{ duration: 0.4 }}
                    >
                      <RepurposeOptions />
                    </motion.div>
                  )}
                </AnimatePresence>
                <AnimatePresence mode="wait">
                  {linkedin.repurposedContent && (
                    <ContentPreview />
                  )}
                </AnimatePresence>
              </TabsContent>
            </Tabs>
          </motion.div>
        </motion.div>
      </main>

      <motion.footer
        className="border-t py-6 bg-muted/30"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.8 }}
      >
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex items-center justify-center gap-4 text-xs">
              <button
                onClick={() => setPrivacyOpen(true)}
                className="text-muted-foreground hover:text-foreground underline-offset-4 hover:underline transition-all duration-200 hover:scale-105"
              >
                Privacy Notice
              </button>
              <span className="text-muted-foreground/50">|</span>
              <button
                onClick={() => setTermsOpen(true)}
                className="text-muted-foreground hover:text-foreground underline-offset-4 hover:underline transition-all duration-200 hover:scale-105"
              >
                Terms & Conditions
              </button>
            </div>
          </div>
        </div>
      </motion.footer>

      <TermsModal open={termsOpen} onOpenChange={setTermsOpen} />
      <PrivacyModal open={privacyOpen} onOpenChange={setPrivacyOpen} />
    </div>
  )
}

export default App
