import { motion } from "framer-motion"
import { Linkedin, Github, CheckCircle2, Key } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ThemeToggle } from "@/components/ui/theme-toggle"
import { useAppStore } from "@/store/appStore"

export function Header() {
  const { claudeAuth, openaiAuth } = useAppStore()

  const isAnyConnected = claudeAuth.isConnected || openaiAuth.isConnected
  const connectedProviders: string[] = []
  if (claudeAuth.isConnected) connectedProviders.push("Claude")
  if (openaiAuth.isConnected) connectedProviders.push("OpenAI")

  return (
    <header className="border-b bg-background/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <motion.div
          className="flex items-center gap-2 cursor-default"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4 }}
        >
          <motion.div
            whileHover={{ rotate: [0, -10, 10, 0], scale: 1.1 }}
            transition={{ duration: 0.4 }}
          >
            <Linkedin className="h-6 w-6 text-primary" />
          </motion.div>
          <h1 className="text-xl font-semibold bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text">
            LinkedIn Content Generator
          </h1>
        </motion.div>
        <motion.div
          className="flex items-center gap-4"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
        >
          {isAnyConnected ? (
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: "spring", stiffness: 200 }}
            >
              <Badge className="bg-green-500 hover:bg-green-600 text-white gap-1 shadow-lg shadow-green-500/25">
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ repeat: Infinity, duration: 2 }}
                >
                  <CheckCircle2 className="h-3 w-3" />
                </motion.div>
                {connectedProviders.join(" + ")} Ready
              </Badge>
            </motion.div>
          ) : (
            <Badge variant="outline" className="gap-1 text-muted-foreground">
              <Key className="h-3 w-3" />
              No AI Connected
            </Badge>
          )}
          <ThemeToggle />
          <Button variant="ghost" size="icon" asChild className="hover:rotate-12 transition-transform duration-200">
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              aria-label="GitHub"
            >
              <Github className="h-5 w-5" />
            </a>
          </Button>
        </motion.div>
      </div>
    </header>
  )
}
