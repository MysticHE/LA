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
          <DialogTitle className="text-2xl">Privacy Notice</DialogTitle>
          <DialogDescription>
            How we handle your data | Last Updated: January 2026
          </DialogDescription>
        </DialogHeader>

        <div className="overflow-y-auto flex-1 pr-2 -mr-2">
          <div className="space-y-6 text-sm">
            {/* Introduction */}
            <section>
              <h3 className="text-base font-semibold mb-2">Overview</h3>
              <p className="text-muted-foreground leading-relaxed">
                LinkedIn Content Generator is committed to protecting your privacy. This notice explains how we collect,
                use, and safeguard your information when you use our Service.
              </p>
            </section>

            {/* Data Collection */}
            <section>
              <h3 className="text-base font-semibold mb-2">Data We Collect</h3>
              <div className="space-y-3">
                <div className="bg-muted/50 p-3 rounded-md">
                  <p className="text-xs font-medium mb-2">API Keys</p>
                  <ul className="list-disc list-inside text-xs text-muted-foreground space-y-1">
                    <li>Your OpenAI and/or Anthropic API keys</li>
                    <li>Encrypted using AES-256 encryption</li>
                    <li>Stored temporarily on our servers for session use only</li>
                    <li>Automatically deleted after 24 hours of inactivity</li>
                  </ul>
                </div>

                <div className="bg-muted/50 p-3 rounded-md">
                  <p className="text-xs font-medium mb-2">GitHub Data</p>
                  <ul className="list-disc list-inside text-xs text-muted-foreground space-y-1">
                    <li>Repository information you choose to analyze</li>
                    <li>Processed temporarily for content generation</li>
                    <li>Not stored permanently on our servers</li>
                  </ul>
                </div>

                <div className="bg-muted/50 p-3 rounded-md">
                  <p className="text-xs font-medium mb-2">Usage Data</p>
                  <ul className="list-disc list-inside text-xs text-muted-foreground space-y-1">
                    <li>Pages visited and features used</li>
                    <li>Browser type and device information</li>
                    <li>Used to improve service performance</li>
                  </ul>
                </div>
              </div>
            </section>

            {/* Data We Don't Collect */}
            <section>
              <h3 className="text-base font-semibold mb-2">Data We Do NOT Collect</h3>
              <ul className="list-disc list-inside text-xs text-muted-foreground space-y-1">
                <li>We do not permanently store your API keys on our servers</li>
                <li>We do not store your GitHub repository content</li>
                <li>We do not log or have access to your generated content</li>
                <li>We do not collect personal identification information</li>
                <li>We do not sell or share your data with third parties</li>
              </ul>
            </section>

            {/* Cross-Border Transfer */}
            <section>
              <h3 className="text-base font-semibold mb-2">Cross-Border Data Transfer</h3>
              <div className="bg-amber-500/10 border border-amber-500/30 p-3 rounded-md">
                <p className="text-xs font-medium mb-2">Important Notice</p>
                <p className="text-xs text-muted-foreground">
                  When you use this service, your API keys are transmitted to:
                </p>
                <ul className="list-disc list-inside text-xs text-muted-foreground mt-2 space-y-1">
                  <li><strong>Anthropic (USA)</strong> - For Claude AI processing</li>
                  <li><strong>OpenAI (USA)</strong> - For GPT AI processing</li>
                </ul>
                <p className="text-xs text-muted-foreground mt-2">
                  By connecting your API key, you consent to this data transfer to the United States.
                </p>
              </div>
            </section>

            {/* Data Security */}
            <section>
              <h3 className="text-base font-semibold mb-2">Data Security</h3>
              <p className="text-muted-foreground leading-relaxed text-xs mb-3">
                We implement industry-standard security measures to protect your data:
              </p>
              <ul className="list-disc list-inside text-xs text-muted-foreground space-y-1">
                <li>AES-256 encryption for API keys</li>
                <li>HTTPS/TLS encryption for all data in transit</li>
                <li>Automatic deletion of session data after 24 hours</li>
                <li>No permanent storage of sensitive credentials</li>
              </ul>
            </section>

            {/* Third-Party Services */}
            <section>
              <h3 className="text-base font-semibold mb-2">Third-Party Services</h3>
              <p className="text-muted-foreground leading-relaxed text-xs mb-3">
                The Service integrates with the following third-party services. Your use of these services is governed
                by their respective privacy policies:
              </p>
              <ul className="space-y-2 text-xs">
                <li>
                  <a href="https://openai.com/privacy" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                    OpenAI Privacy Policy
                  </a>
                </li>
                <li>
                  <a href="https://www.anthropic.com/privacy" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                    Anthropic Privacy Policy
                  </a>
                </li>
                <li>
                  <a href="https://docs.github.com/en/site-policy/privacy-policies/github-privacy-statement" target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                    GitHub Privacy Statement
                  </a>
                </li>
              </ul>
            </section>

            {/* Singapore PDPA */}
            <section>
              <h3 className="text-base font-semibold mb-2">Singapore PDPA Compliance</h3>
              <p className="text-muted-foreground leading-relaxed text-xs mb-3">
                We are committed to protecting your personal data in accordance with the Personal Data Protection
                Act 2012 (PDPA) of Singapore.
              </p>
              <div className="bg-muted/50 p-3 rounded-md">
                <p className="text-xs font-medium mb-2">Your Rights Under PDPA</p>
                <ul className="list-disc list-inside text-xs text-muted-foreground space-y-1">
                  <li><strong>Access:</strong> Request access to your personal data</li>
                  <li><strong>Correction:</strong> Request correction of inaccurate data</li>
                  <li><strong>Withdrawal:</strong> Withdraw consent for data collection/use</li>
                </ul>
              </div>
            </section>

            {/* Data Breach */}
            <section>
              <h3 className="text-base font-semibold mb-2">Data Breach Notification</h3>
              <p className="text-muted-foreground leading-relaxed text-xs">
                In the event of a data breach affecting your personal data, we will notify the Personal Data Protection
                Commission within 3 calendar days as required by law and notify you directly if the breach is likely
                to result in significant harm.
              </p>
            </section>

            {/* Generated Content */}
            <section>
              <h3 className="text-base font-semibold mb-2">Generated Content</h3>
              <p className="text-muted-foreground leading-relaxed text-xs">
                All content generation happens via your own API keys. We do not store, log, or have access to the
                LinkedIn posts or other content generated by the Service. Generated content is processed in real-time
                and is not retained after your session.
              </p>
            </section>

            {/* Contact */}
            <section>
              <h3 className="text-base font-semibold mb-2">Contact Us</h3>
              <p className="text-muted-foreground leading-relaxed text-xs">
                If you have questions about this Privacy Notice or wish to exercise your data protection rights,
                please contact us through the information provided on our website.
              </p>
            </section>

            {/* Disclaimer */}
            <section className="border-t pt-4">
              <div className="bg-muted/50 p-3 rounded-md">
                <p className="text-[10px] text-muted-foreground">
                  This Privacy Notice may be updated from time to time. We will notify users of any material changes
                  by updating the "Last Updated" date at the top of this notice.
                </p>
              </div>
            </section>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
