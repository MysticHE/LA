import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { Search, Loader2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useAppStore } from "@/store/appStore"
import { useAnalyzeRepo } from "@/hooks/useAnalyzeRepo"

const formSchema = z.object({
  url: z
    .string()
    .min(1, "Please enter a GitHub URL")
    .regex(
      /^https?:\/\/(www\.)?github\.com\/[\w-]+\/[\w.-]+\/?$/,
      "Please enter a valid GitHub repository URL"
    ),
})

type FormData = z.infer<typeof formSchema>

export function RepoInputForm() {
  const { isAnalyzing, error } = useAppStore()
  const analyzeRepo = useAnalyzeRepo()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormData>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      url: "",
    },
  })

  const onSubmit = (data: FormData) => {
    analyzeRepo.mutate(data.url)
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <span className="text-2xl">1</span>
          Enter GitHub Repository
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="flex gap-2">
            <div className="flex-1">
              <Input
                placeholder="https://github.com/username/repository"
                {...register("url")}
                disabled={isAnalyzing}
              />
              {errors.url && (
                <p className="text-sm text-destructive mt-1">
                  {errors.url.message}
                </p>
              )}
            </div>
            <Button type="submit" disabled={isAnalyzing}>
              {isAnalyzing ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                <>
                  <Search className="h-4 w-4" />
                  Analyze
                </>
              )}
            </Button>
          </div>
          {error && (
            <p className="text-sm text-destructive bg-destructive/10 p-3 rounded-md">
              {error}
            </p>
          )}
        </form>
      </CardContent>
    </Card>
  )
}
