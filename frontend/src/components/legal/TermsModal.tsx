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
          <DialogTitle className="text-2xl">Terms and Conditions</DialogTitle>
          <DialogDescription>
            Last Updated: January 2026 | Version 1.0
          </DialogDescription>
        </DialogHeader>

        <div className="overflow-y-auto flex-1 pr-2 -mr-2">
          <div className="space-y-6 text-sm">
            {/* Section 1 */}
            <section>
              <h3 className="text-base font-semibold mb-2">1. Introduction</h3>
              <p className="text-muted-foreground leading-relaxed">
                These Terms and Conditions ("Terms") govern your access to and use of LinkedIn Content Generator ("Service"),
                a personal project accessible at linkedin-content-frontend-smfw.onrender.com ("Website").
              </p>
              <p className="text-muted-foreground leading-relaxed mt-2">
                By accessing or using the Service, you agree to be bound by these Terms. If you disagree with any part
                of these Terms, you may not access the Service.
              </p>
              <div className="bg-muted/50 p-3 rounded-md mt-3">
                <p className="text-xs font-medium">
                  This is a personal project and is not operated by a registered company. The Service is provided on
                  an "as is" basis without any guarantees of availability, support, or continued operation.
                </p>
              </div>
            </section>

            {/* Section 2 */}
            <section>
              <h3 className="text-base font-semibold mb-2">2. Definitions</h3>
              <ul className="space-y-1.5 text-muted-foreground text-xs">
                <li><strong>"Service"</strong> - The LinkedIn Content Generator web application</li>
                <li><strong>"User," "you," "your"</strong> - Any individual accessing or using the Service</li>
                <li><strong>"Generated Content"</strong> - LinkedIn posts created by the Service using AI</li>
                <li><strong>"API Keys"</strong> - Authentication credentials for third-party AI services</li>
                <li><strong>"Personal Data"</strong> - Information that identifies or could identify an individual</li>
              </ul>
            </section>

            {/* Section 3 */}
            <section>
              <h3 className="text-base font-semibold mb-2">3. Service Description</h3>
              <p className="text-muted-foreground leading-relaxed">
                LinkedIn Content Generator is a free tool that analyzes GitHub repositories and generates LinkedIn
                post content using AI (OpenAI GPT or Anthropic Claude). You provide your own API keys, connect
                your GitHub repositories, and the Service generates content suggestions for your review.
              </p>
            </section>

            {/* Section 4 */}
            <section>
              <h3 className="text-base font-semibold mb-2">4. User Eligibility</h3>
              <p className="text-muted-foreground leading-relaxed">
                To use this Service, you must be at least 18 years old, have the legal capacity to enter into binding
                agreements, and have valid API keys from OpenAI and/or Anthropic obtained directly from those providers.
              </p>
            </section>

            {/* Section 5 */}
            <section>
              <h3 className="text-base font-semibold mb-2">5. API Keys and Third-Party Services</h3>
              <div className="bg-destructive/10 border border-destructive/20 p-3 rounded-md">
                <p className="text-xs font-medium mb-2">You are solely responsible for:</p>
                <ul className="list-disc list-inside text-xs space-y-1 text-muted-foreground">
                  <li>Obtaining API keys directly from providers</li>
                  <li>Complying with OpenAI's and Anthropic's terms of service</li>
                  <li>All costs and charges incurred through your API usage</li>
                  <li>Maintaining the security of your API keys</li>
                </ul>
              </div>
              <p className="text-muted-foreground leading-relaxed mt-3 text-xs">
                Your API keys are stored in your browser's local storage and encrypted. We do not store your API keys
                on our servers permanently.
              </p>
            </section>

            {/* Section 6 */}
            <section>
              <h3 className="text-base font-semibold mb-2">6. AI-Generated Content Disclaimer</h3>
              <div className="bg-amber-500/10 border border-amber-500/30 p-3 rounded-md">
                <p className="text-xs font-medium mb-2">Important Notice</p>
                <ul className="list-disc list-inside text-xs space-y-1 text-muted-foreground">
                  <li>AI-generated content may contain inaccuracies or errors</li>
                  <li>Content should be reviewed and edited before use</li>
                  <li>You are responsible for all content you publish</li>
                  <li>Generated content does not constitute professional advice</li>
                </ul>
              </div>
            </section>

            {/* Section 7 */}
            <section>
              <h3 className="text-base font-semibold mb-2">7. Acceptable Use</h3>
              <p className="text-muted-foreground leading-relaxed text-xs">
                The Service is for personal, non-commercial content creation. You may not use it for illegal purposes,
                generate harmful or misleading content, reverse engineer the Service, or use automated systems to
                abuse the Service.
              </p>
            </section>

            {/* Section 8 */}
            <section>
              <h3 className="text-base font-semibold mb-2">8. Privacy and Data Protection</h3>
              <p className="text-muted-foreground leading-relaxed text-xs">
                We are committed to protecting your personal data in accordance with the Personal Data Protection
                Act 2012 (PDPA) of Singapore. You have the right to access your personal data, correct inaccurate
                data, and withdraw consent for data collection/use.
              </p>
            </section>

            {/* Section 9 */}
            <section>
              <h3 className="text-base font-semibold mb-2">9. Disclaimers</h3>
              <div className="bg-muted p-3 rounded-md">
                <p className="text-xs text-muted-foreground">
                  THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS
                  OR IMPLIED. We do not guarantee uninterrupted service, accurate generated content, or continued availability.
                </p>
              </div>
            </section>

            {/* Section 10 */}
            <section>
              <h3 className="text-base font-semibold mb-2">10. Limitation of Liability</h3>
              <p className="text-muted-foreground leading-relaxed text-xs">
                To the maximum extent permitted by Singapore law, we shall not be liable for any indirect, incidental,
                special, consequential, or punitive damages. Our total aggregate liability shall not exceed S$100.
                Nothing excludes liability for death or personal injury caused by negligence or fraud.
              </p>
            </section>

            {/* Section 11 */}
            <section>
              <h3 className="text-base font-semibold mb-2">11. Indemnification</h3>
              <p className="text-muted-foreground leading-relaxed text-xs">
                You agree to indemnify and hold harmless the operator of this Service from any claims arising from
                your use of the Service, violation of these Terms, or content you generate and publish.
              </p>
            </section>

            {/* Section 12 */}
            <section>
              <h3 className="text-base font-semibold mb-2">12. Termination</h3>
              <p className="text-muted-foreground leading-relaxed text-xs">
                You may stop using the Service at any time by clearing your browser's local storage. We may suspend
                or terminate access at any time without notice for any reason, including Terms violations.
              </p>
            </section>

            {/* Section 13 */}
            <section>
              <h3 className="text-base font-semibold mb-2">13. Dispute Resolution</h3>
              <p className="text-muted-foreground leading-relaxed text-xs">
                These Terms shall be governed by the laws of the Republic of Singapore. Any disputes shall be subject
                to the exclusive jurisdiction of the courts of Singapore.
              </p>
            </section>

            {/* Section 14 */}
            <section>
              <h3 className="text-base font-semibold mb-2">14. General Provisions</h3>
              <ul className="space-y-1 text-muted-foreground text-xs">
                <li><strong>Entire Agreement:</strong> These Terms constitute the entire agreement regarding the Service.</li>
                <li><strong>Severability:</strong> Unenforceable provisions do not affect remaining provisions.</li>
                <li><strong>Amendments:</strong> We may modify these Terms at any time by posting updated Terms.</li>
              </ul>
            </section>

            {/* Disclaimer */}
            <section className="border-t pt-4">
              <div className="bg-muted/50 p-3 rounded-md">
                <p className="text-[10px] text-muted-foreground">
                  <strong>DISCLAIMER:</strong> This Terms and Conditions document was generated as a template and should
                  be reviewed by a qualified legal professional before use. This document does not constitute legal advice.
                </p>
              </div>
            </section>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
