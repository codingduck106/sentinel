/** Opt-in for the AI explanation, with the disclosure. Off by default; never changes the rating.
 *  The key facts stay visible next to the box; the full masking detail is one click away. */
export function AiOptIn({ checked, onChange, id = "ai-optin" }: { checked: boolean; onChange: (v: boolean) => void; id?: string }) {
  return (
    <div className="ai-optin">
      <input id={id} type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} aria-describedby={`${id}-desc`} />
      <label htmlFor={id}>Also get an AI explanation (optional)</label>
      <div id={`${id}-desc`} className="soft">
        <p>
          Sends your message to <strong>Anthropic</strong> (Claude). Numbers and emails are masked; names and links are not.
          It doesn&rsquo;t change the rating.
        </p>
        <details className="ai-more">
          <summary>What gets masked</summary>
          <p>
            Recognized digit sequences, phone/account-like numbers, email addresses, and labeled PIN/OTP/CVV codes are masked first.
            Names, postal addresses, link domains, and other words are not removed; unlabeled short numbers may remain. Sentinel
            doesn&rsquo;t store it; Anthropic handles it under its{" "}
            <a href="https://www.anthropic.com/legal/privacy" target="_blank" rel="noopener noreferrer">privacy policy</a>.
          </p>
        </details>
      </div>
    </div>
  );
}
