import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"

interface TermsModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function TermsModal({ open, onOpenChange }: TermsModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-xl">Terms of Use</DialogTitle>
          <DialogDescription>
            Last Updated: January 2026
          </DialogDescription>
        </DialogHeader>

        <div className="overflow-y-auto flex-1 pr-2 -mr-2">
          <div className="space-y-5 text-sm">
            <section>
              <h3 className="font-medium mb-2">About This Service</h3>
              <p className="text-muted-foreground text-xs leading-relaxed">
                LinkedIn Content Generator helps you create LinkedIn posts from your GitHub repositories
                using AI. You provide your own API keys from OpenAI or Anthropic.
              </p>
            </section>

            <section>
              <h3 className="font-medium mb-2">Your Responsibilities</h3>
              <ul className="list-disc list-inside text-xs text-muted-foreground space-y-1">
                <li>Obtain API keys directly from OpenAI or Anthropic</li>
                <li>Review generated content before publishing</li>
                <li>Comply with the terms of your AI provider</li>
              </ul>
            </section>

            <section>
              <h3 className="font-medium mb-2">API Keys</h3>
              <p className="text-muted-foreground text-xs leading-relaxed">
                Your API keys are encrypted and used only during your active session.
                You are responsible for any costs from your AI provider.
              </p>
            </section>

            <section>
              <h3 className="font-medium mb-2">Generated Content</h3>
              <p className="text-muted-foreground text-xs leading-relaxed">
                AI-generated content may contain errors. Always review and edit before publishing.
                You are responsible for content you choose to publish.
              </p>
            </section>

            <section>
              <h3 className="font-medium mb-2">Service Availability</h3>
              <p className="text-muted-foreground text-xs leading-relaxed">
                This is a personal project provided as-is. We do not guarantee uptime or availability.
              </p>
            </section>

            <section>
              <h3 className="font-medium mb-2">Acceptable Use</h3>
              <p className="text-muted-foreground text-xs leading-relaxed">
                Use this service for legitimate content creation only. Do not use it for spam,
                misleading content, or any illegal purpose.
              </p>
            </section>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
