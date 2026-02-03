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
                using AI. You provide your own API keys from OpenAI, Anthropic, or Google.
              </p>
            </section>

            <section>
              <h3 className="font-medium mb-2">Your Responsibilities</h3>
              <ul className="list-disc list-inside text-xs text-muted-foreground space-y-1">
                <li>Obtain API keys directly from OpenAI, Anthropic, or Google</li>
                <li>Review generated content before publishing</li>
                <li>Comply with the terms of your AI provider</li>
                <li>Comply with LinkedIn's terms of service when posting</li>
              </ul>
            </section>

            <section>
              <h3 className="font-medium mb-2">API Keys & Security</h3>
              <p className="text-muted-foreground text-xs leading-relaxed mb-2">
                Your API keys are protected with AES-256 encryption and bound to your browser session.
                We never store your keys in plaintext or in any database.
              </p>
              <ul className="list-disc list-inside text-xs text-muted-foreground space-y-1">
                <li>Keys are encrypted immediately upon entry</li>
                <li>Keys auto-expire after 24 hours of inactivity</li>
                <li>Keys are permanently deleted when you disconnect</li>
                <li>You are responsible for any costs from your AI provider</li>
              </ul>
              <p className="text-muted-foreground text-xs leading-relaxed mt-2">
                <strong>Tip:</strong> For added security, consider creating API keys with usage limits in your provider's dashboard.
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

            <section>
              <h3 className="font-medium mb-2">Limitation of Liability</h3>
              <p className="text-muted-foreground text-xs leading-relaxed">
                This service is provided "as is" without warranties of any kind.
                We are not liable for any damages arising from your use of this service,
                including costs incurred from AI providers.
              </p>
            </section>

            <section>
              <h3 className="font-medium mb-2">Changes</h3>
              <p className="text-muted-foreground text-xs leading-relaxed">
                We may update these terms at any time. Continued use after changes constitutes acceptance.
              </p>
            </section>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
