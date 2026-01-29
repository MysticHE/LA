import { motion } from "framer-motion"
import { Star, GitFork, Code, Sparkles, Zap, AlertCircle, FileText } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useAppStore } from "@/store/appStore"
import type { ProjectInsight } from "@/lib/api"

const categoryColors: Record<string, string> = {
  language: "bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-800 hover:bg-blue-500/20",
  framework: "bg-purple-500/10 text-purple-700 dark:text-purple-400 border-purple-200 dark:border-purple-800 hover:bg-purple-500/20",
  library: "bg-green-500/10 text-green-700 dark:text-green-400 border-green-200 dark:border-green-800 hover:bg-green-500/20",
  tool: "bg-orange-500/10 text-orange-700 dark:text-orange-400 border-orange-200 dark:border-orange-800 hover:bg-orange-500/20",
  database: "bg-red-500/10 text-red-700 dark:text-red-400 border-red-200 dark:border-red-800 hover:bg-red-500/20",
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.1 }
  }
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: "easeOut" as const } }
}

function InsightItem({ insight }: { insight: ProjectInsight }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-start gap-2"
    >
      <span className="text-sm shrink-0">{insight.icon}</span>
      <div className="min-w-0">
        <p className="text-sm font-medium">{insight.title}</p>
        <p className="text-xs text-muted-foreground">{insight.description}</p>
      </div>
    </motion.div>
  )
}

export function AnalysisCard() {
  const { analysis, isAnalyzing } = useAppStore()

  if (isAnalyzing) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <span className="text-2xl">2</span>
            Project Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-4 w-3/4" />
          <div className="flex gap-2">
            <Skeleton className="h-6 w-20" />
            <Skeleton className="h-6 w-20" />
            <Skeleton className="h-6 w-20" />
          </div>
          <Skeleton className="h-20 w-full" />
        </CardContent>
      </Card>
    )
  }

  if (!analysis) {
    return null
  }

  // Filter insights by type (highlights are now merged into features)
  const strengths = analysis.insights.filter(i => i.type === "strength")
  const considerations = analysis.insights.filter(i => i.type === "consideration")

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      <Card>
        <CardHeader>
          <motion.div variants={itemVariants}>
            <CardTitle className="text-lg flex items-center gap-2">
              <span className="text-2xl bg-gradient-to-br from-primary to-primary/60 bg-clip-text text-transparent">2</span>
              Project Analysis
            </CardTitle>
          </motion.div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Metadata row */}
          <motion.div variants={itemVariants} className="flex items-center justify-between">
            <h3 className="text-xl font-semibold">{analysis.repo_name}</h3>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span className="flex items-center gap-1 hover:text-yellow-500 transition-colors cursor-default">
                <Star className="h-4 w-4" />
                {analysis.stars.toLocaleString()}
              </span>
              <span className="flex items-center gap-1 hover:text-primary transition-colors cursor-default">
                <GitFork className="h-4 w-4" />
                {analysis.forks.toLocaleString()}
              </span>
              {analysis.language && (
                <span className="flex items-center gap-1 hover:text-green-500 transition-colors cursor-default">
                  <Code className="h-4 w-4" />
                  {analysis.language}
                </span>
              )}
            </div>
          </motion.div>

          {analysis.description && (
            <motion.p variants={itemVariants} className="text-muted-foreground text-sm">{analysis.description}</motion.p>
          )}

          {/* 2x2 Grid Layout */}
          <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Tech Stack */}
            <div className="p-4 bg-muted/30 rounded-lg">
              <h4 className="font-medium mb-3 flex items-center gap-2 text-sm">
                <Code className="h-4 w-4" /> Tech Stack
              </h4>
              <div className="flex flex-wrap gap-2">
                {analysis.tech_stack.map((tech, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: i * 0.03, duration: 0.2 }}
                  >
                    <Badge
                      variant="outline"
                      className={`cursor-default transition-all duration-200 text-xs ${categoryColors[tech.category] || ""}`}
                    >
                      {tech.name}
                    </Badge>
                  </motion.div>
                ))}
                {analysis.tech_stack.length === 0 && (
                  <span className="text-xs text-muted-foreground">
                    No technologies detected
                  </span>
                )}
              </div>
            </div>

            {/* Features & Highlights (merged) */}
            <div className="p-4 bg-muted/30 rounded-lg">
              <h4 className="font-medium mb-3 flex items-center gap-2 text-sm">
                <Zap className="h-4 w-4" /> Features & Highlights
              </h4>
              <ul className="space-y-1">
                {analysis.features.slice(0, 6).map((feature, i) => (
                  <motion.li
                    key={i}
                    className="text-xs flex items-start gap-2 text-muted-foreground hover:text-foreground transition-colors"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.05, duration: 0.2 }}
                  >
                    <span className="text-primary mt-0.5">•</span>
                    <span>{feature.name}</span>
                  </motion.li>
                ))}
                {analysis.features.length === 0 && (
                  <span className="text-xs text-muted-foreground">
                    No features detected
                  </span>
                )}
              </ul>
            </div>

            {/* Strengths */}
            <div className="p-4 bg-green-500/10 rounded-lg border border-green-500/20">
              <h4 className="font-medium mb-3 flex items-center gap-2 text-sm text-green-600 dark:text-green-400">
                <Sparkles className="h-4 w-4" /> Strengths
              </h4>
              {strengths.length > 0 ? (
                <div className="space-y-2">
                  {strengths.slice(0, 4).map((insight, i) => (
                    <InsightItem key={i} insight={insight} />
                  ))}
                </div>
              ) : (
                <span className="text-xs text-muted-foreground">
                  No strengths detected
                </span>
              )}
            </div>

            {/* Considerations */}
            <div className="p-4 bg-amber-500/10 rounded-lg border border-amber-500/20">
              <h4 className="font-medium mb-3 flex items-center gap-2 text-sm text-amber-600 dark:text-amber-400">
                <AlertCircle className="h-4 w-4" /> Considerations
              </h4>
              {considerations.length > 0 ? (
                <div className="space-y-2">
                  {considerations.slice(0, 4).map((insight, i) => (
                    <InsightItem key={i} insight={insight} />
                  ))}
                </div>
              ) : (
                <span className="text-xs text-muted-foreground">
                  No considerations detected
                </span>
              )}
            </div>
          </motion.div>

          {/* AI Summary Footer */}
          {(analysis.ai_summary || analysis.readme_summary) && (
            <motion.div
              variants={itemVariants}
              className="p-3 bg-muted/20 rounded-lg border-t border-border/50"
            >
              <p className="text-sm text-muted-foreground flex items-start gap-2">
                <FileText className="h-4 w-4 mt-0.5 shrink-0" />
                <span>
                  <span className="font-medium text-foreground">Summary: </span>
                  {analysis.ai_summary || analysis.readme_summary}
                </span>
              </p>
            </motion.div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}
