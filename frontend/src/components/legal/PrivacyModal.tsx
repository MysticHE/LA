import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog"

interface PrivacyModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function PrivacyModal({ open, onOpenChange }: PrivacyModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="text-xl">Privacy Notice</DialogTitle>
          <DialogDescription>
            Last Updated: January 2026
          </DialogDescription>
        </DialogHeader>

        <div className="overflow-y-auto flex-1 pr-2 -mr-2">
          <div className="space-y-5 text-sm">
            <section>
              <h3 className="font-medium mb-2">What We Collect</h3>
              <ul className="list-disc list-inside text-xs text-muted-foreground space-y-1">
                <li>API keys you provide (AES-256 encrypted, session-bound)</li>
                <li>Session ID stored in your browser (localStorage)</li>
                <li>GitHub repository URLs you analyze (not stored)</li>
              </ul>
            </section>

            <section>
              <h3 className="font-medium mb-2">What We Don't Collect</h3>
              <ul className="list-disc list-inside text-xs text-muted-foreground space-y-1">
                <li>Personal information or accounts</li>
                <li>Generated content</li>
                <li>Permanent storage of API keys</li>
              </ul>
            </section>

            <section>
              <h3 className="font-medium mb-2">How Your Data Is Used</h3>
              <p className="text-muted-foreground text-xs leading-relaxed mb-2">
                Your API keys are used solely to communicate with AI providers (OpenAI, Anthropic, Google)
                to generate content on your behalf.
              </p>
              <ul className="list-disc list-inside text-xs text-muted-foreground space-y-1">
                <li>Keys are encrypted with AES-256 and bound to your session</li>
                <li>Keys auto-expire after 24 hours of inactivity</li>
                <li>Keys are permanently deleted when you click "Disconnect"</li>
                <li>We never log, share, or access your plaintext API keys</li>
              </ul>
            </section>

            <section>
              <h3 className="font-medium mb-2">Third-Party Services</h3>
              <p className="text-muted-foreground text-xs leading-relaxed mb-2">
                This service uses your API keys with:
              </p>
              <ul className="space-y-1 text-xs">
                <li>
                  <a href="https://openai.com/privacy" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                    OpenAI
                  </a>
                </li>
                <li>
                  <a href="https://www.anthropic.com/privacy" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                    Anthropic
                  </a>
                </li>
                <li>
                  <a href="https://policies.google.com/privacy" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                    Google
                  </a>
                </li>
              </ul>
            </section>

            <section>
              <h3 className="font-medium mb-2">Questions</h3>
              <p className="text-muted-foreground text-xs leading-relaxed">
                For privacy questions, please contact us through the project repository.
              </p>
            </section>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
