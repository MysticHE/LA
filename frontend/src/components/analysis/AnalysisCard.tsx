import { motion } from "framer-motion"
import { Star, GitFork, Code, Sparkles, Zap, Info } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion"
import { useAppStore } from "@/store/appStore"
import type { ProjectInsight, InsightType } from "@/lib/api"

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

const insightTypeConfig: Record<InsightType, { icon: React.ReactNode; label: string; bgClass: string; borderClass: string }> = {
  strength: {
    icon: <Sparkles className="h-4 w-4" />,
    label: "Strengths",
    bgClass: "bg-green-500/10",
    borderClass: "border-green-200 dark:border-green-800",
  },
  highlight: {
    icon: <Zap className="h-4 w-4" />,
    label: "Highlights",
    bgClass: "bg-blue-500/10",
    borderClass: "border-blue-200 dark:border-blue-800",
  },
  consideration: {
    icon: <Info className="h-4 w-4" />,
    label: "Considerations",
    bgClass: "bg-amber-500/10",
    borderClass: "border-amber-200 dark:border-amber-800",
  },
}

function InsightCard({ insight }: { insight: ProjectInsight }) {
  const config = insightTypeConfig[insight.type]
  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      className={`flex items-start gap-3 p-3 rounded-lg ${config.bgClass} border ${config.borderClass}`}
    >
      <span className="text-lg shrink-0">{insight.icon}</span>
      <div className="min-w-0">
        <p className="font-medium text-sm">{insight.title}</p>
        <p className="text-xs text-muted-foreground">{insight.description}</p>
      </div>
    </motion.div>
  )
}

function groupInsightsByType(insights: ProjectInsight[]) {
  return {
    strengths: insights.filter(i => i.type === "strength"),
    highlights: insights.filter(i => i.type === "highlight"),
    considerations: insights.filter(i => i.type === "consideration"),
  }
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
        <CardContent className="space-y-6">
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
            <motion.p variants={itemVariants} className="text-muted-foreground">{analysis.description}</motion.p>
          )}

          <div className="grid md:grid-cols-2 gap-6">
            <motion.div variants={itemVariants}>
              <h4 className="font-medium mb-3">Tech Stack</h4>
              <motion.div
                className="flex flex-wrap gap-2"
                variants={containerVariants}
              >
                {analysis.tech_stack.map((tech, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: i * 0.05, duration: 0.2 }}
                  >
                    <Badge
                      variant="outline"
                      className={`cursor-default transition-all duration-200 ${categoryColors[tech.category] || ""}`}
                    >
                      {tech.name}
                    </Badge>
                  </motion.div>
                ))}
                {analysis.tech_stack.length === 0 && (
                  <span className="text-sm text-muted-foreground">
                    No technologies detected
                  </span>
                )}
              </motion.div>
            </motion.div>

            <motion.div variants={itemVariants}>
              <h4 className="font-medium mb-3">Key Features</h4>
              <ul className="space-y-1">
                {analysis.features.slice(0, 5).map((feature, i) => (
                  <motion.li
                    key={i}
                    className="text-sm flex items-start gap-2 hover:text-foreground transition-colors"
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.1, duration: 0.3 }}
                  >
                    <span className="text-primary mt-1">•</span>
                    <span>{feature.name}</span>
                  </motion.li>
                ))}
                {analysis.features.length === 0 && (
                  <span className="text-sm text-muted-foreground">
                    No features detected
                  </span>
                )}
              </ul>
            </motion.div>
          </div>

          {analysis.readme_summary && (
            <motion.div variants={itemVariants}>
              <h4 className="font-medium mb-2">Summary</h4>
              <p className="text-sm text-muted-foreground leading-relaxed">
                {analysis.readme_summary}
              </p>
            </motion.div>
          )}

          {analysis.insights && analysis.insights.length > 0 && (
            <motion.div variants={itemVariants}>
              <h4 className="font-medium mb-3">Project Insights</h4>
              <ProjectInsightsAccordion insights={analysis.insights} />
            </motion.div>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}

function ProjectInsightsAccordion({ insights }: { insights: ProjectInsight[] }) {
  const grouped = groupInsightsByType(insights)
  const defaultOpen: string[] = []

  if (grouped.strengths.length > 0) defaultOpen.push("strengths")

  return (
    <Accordion type="multiple" defaultValue={defaultOpen} className="w-full">
      {grouped.strengths.length > 0 && (
        <AccordionItem value="strengths" className="border-green-200 dark:border-green-800">
          <AccordionTrigger className="hover:no-underline py-3">
            <div className="flex items-center gap-2 text-green-700 dark:text-green-400">
              <Sparkles className="h-4 w-4" />
              <span className="font-medium">Strengths</span>
              <Badge variant="secondary" className="bg-green-500/20 text-green-700 dark:text-green-400 text-xs">
                {grouped.strengths.length}
              </Badge>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <div className="space-y-2">
              {grouped.strengths.map((insight, i) => (
                <InsightCard key={i} insight={insight} />
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>
      )}

      {grouped.highlights.length > 0 && (
        <AccordionItem value="highlights" className="border-blue-200 dark:border-blue-800">
          <AccordionTrigger className="hover:no-underline py-3">
            <div className="flex items-center gap-2 text-blue-700 dark:text-blue-400">
              <Zap className="h-4 w-4" />
              <span className="font-medium">Highlights</span>
              <Badge variant="secondary" className="bg-blue-500/20 text-blue-700 dark:text-blue-400 text-xs">
                {grouped.highlights.length}
              </Badge>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <div className="space-y-2">
              {grouped.highlights.map((insight, i) => (
                <InsightCard key={i} insight={insight} />
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>
      )}

      {grouped.considerations.length > 0 && (
        <AccordionItem value="considerations" className="border-amber-200 dark:border-amber-800">
          <AccordionTrigger className="hover:no-underline py-3">
            <div className="flex items-center gap-2 text-amber-700 dark:text-amber-400">
              <Info className="h-4 w-4" />
              <span className="font-medium">Considerations</span>
              <Badge variant="secondary" className="bg-amber-500/20 text-amber-700 dark:text-amber-400 text-xs">
                {grouped.considerations.length}
              </Badge>
            </div>
          </AccordionTrigger>
          <AccordionContent>
            <div className="space-y-2">
              {grouped.considerations.map((insight, i) => (
                <InsightCard key={i} insight={insight} />
              ))}
            </div>
          </AccordionContent>
        </AccordionItem>
      )}
    </Accordion>
  )
}
