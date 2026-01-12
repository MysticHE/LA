import { Star, GitFork, Code } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { useAppStore } from "@/store/appStore"

const categoryColors: Record<string, string> = {
  language: "bg-blue-500/10 text-blue-700 border-blue-200",
  framework: "bg-purple-500/10 text-purple-700 border-purple-200",
  library: "bg-green-500/10 text-green-700 border-green-200",
  tool: "bg-orange-500/10 text-orange-700 border-orange-200",
  database: "bg-red-500/10 text-red-700 border-red-200",
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
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <span className="text-2xl">2</span>
          Project Analysis
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="flex items-center justify-between">
          <h3 className="text-xl font-semibold">{analysis.repo_name}</h3>
          <div className="flex items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1">
              <Star className="h-4 w-4" />
              {analysis.stars.toLocaleString()}
            </span>
            <span className="flex items-center gap-1">
              <GitFork className="h-4 w-4" />
              {analysis.forks.toLocaleString()}
            </span>
            {analysis.language && (
              <span className="flex items-center gap-1">
                <Code className="h-4 w-4" />
                {analysis.language}
              </span>
            )}
          </div>
        </div>

        {analysis.description && (
          <p className="text-muted-foreground">{analysis.description}</p>
        )}

        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium mb-3">Tech Stack</h4>
            <div className="flex flex-wrap gap-2">
              {analysis.tech_stack.map((tech, i) => (
                <Badge
                  key={i}
                  variant="outline"
                  className={categoryColors[tech.category] || ""}
                >
                  {tech.name}
                </Badge>
              ))}
              {analysis.tech_stack.length === 0 && (
                <span className="text-sm text-muted-foreground">
                  No technologies detected
                </span>
              )}
            </div>
          </div>

          <div>
            <h4 className="font-medium mb-3">Key Features</h4>
            <ul className="space-y-1">
              {analysis.features.slice(0, 5).map((feature, i) => (
                <li key={i} className="text-sm flex items-start gap-2">
                  <span className="text-primary mt-1">•</span>
                  <span>{feature.name}</span>
                </li>
              ))}
              {analysis.features.length === 0 && (
                <span className="text-sm text-muted-foreground">
                  No features detected
                </span>
              )}
            </ul>
          </div>
        </div>

        {analysis.readme_summary && (
          <div>
            <h4 className="font-medium mb-2">Summary</h4>
            <p className="text-sm text-muted-foreground leading-relaxed">
              {analysis.readme_summary}
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
