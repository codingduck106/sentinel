"use client";

import { Results } from "@/components/Results";
import { AiOptIn } from "@/components/AiOptIn";
import { EXAMPLES, MAX_CHARS, useCheck } from "@/lib/useCheck";

export function CheckClient() {
  const { text, setText, result, error, loading, aiConsent, setAiConsent, ai, inputRef, length, over, submit, loadExample, reset } = useCheck();

  return (
    <>
      <h1>Check a text for scams</h1>
      <p className="lede">Paste the text you received. Include any links or numbers exactly as they appear.</p>

      <form onSubmit={submit} noValidate>
        <div className="composer">
          <label htmlFor="msg" className="visually-hidden">Message to check</label>
          <textarea
            id="msg"
            ref={inputRef}
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Paste the message here"
            aria-describedby="counter"
            aria-invalid={over}
            autoComplete="off"
            spellCheck={false}
          />
          <span id="counter" className={`counter ${over ? "over" : ""}`} aria-live="polite">
            {length} / {MAX_CHARS}{over ? " — too long" : ""}
          </span>
        </div>

        <div className="examples">
          <span className="soft">Or try an example:</span>
          {EXAMPLES.map((ex) => (
            <button key={ex.label} type="button" className="chip" onClick={() => loadExample(ex.text)}>
              {ex.label}
            </button>
          ))}
        </div>

        <AiOptIn checked={aiConsent} onChange={setAiConsent} />

        <div className="submit-row">
          <button type="submit" className="btn" disabled={over || loading} aria-busy={loading}>
            {loading ? <><span className="spinner" aria-hidden />Checking…</> : "Check this message"}
          </button>
          <p className="privacy">We don&rsquo;t store your messages. Checking takes a second{aiConsent ? "; the AI explanation a few more" : ""}.</p>
        </div>
      </form>

      {error && <p className="error" role="alert">{error}</p>}

      {result ? (
        <Results r={result} ai={ai} onReset={reset} />
      ) : (
        !error && (
          <p className="placeholder-panel">
            Your result will appear here: a verdict, the exact words that worry us, and what to do next.
          </p>
        )
      )}
    </>
  );
}
