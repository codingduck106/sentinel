"use client";

import { useEffect, useRef, useState } from "react";
import { AnalyzeError, analyzeMessage, fetchContextual, MAX_CHARS, type AnalyzeResult, type ContextualState } from "@/lib/api";

export const EXAMPLES: { label: string; text: string }[] = [
  { label: "Bank alert", text: "HSBC: We have detected unusual activity on your account. It will be suspended within 24 hours unless you verify immediately at hsbc-secure-check.com" },
  { label: "Prize win", text: "Congratulations! You have won a £1000 Tesco gift card. Claim now at tesco-rewards-uk.com before it expires tonight." },
  { label: "Friend’s message", text: "Hi! Running 10 mins late, grab us a table? x" },
];

/** One message check: input state, the main analysis, and the opt-in AI explanation. Shared by / and /check. */
export function useCheck() {
  const [text, setText] = useState("");
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  // Opt-in AI explanation: off by default, never sent unless ticked, never affects the rating.
  const [aiConsent, setAiConsent] = useState(false);
  const [ai, setAi] = useState<ContextualState | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  // Count code points, like the backend (an emoji is 1 here, 2 in text.length).
  const length = [...text].length;
  const over = length > MAX_CHARS;
  const empty = text.trim().length === 0;

  // Leaving the page mid-check cancels the request.
  useEffect(() => () => abortRef.current?.abort(), []);

  /** Cancel any in-flight check so a late response can't overwrite what the user did next. */
  function cancelPending() {
    abortRef.current?.abort();
    abortRef.current = null;
    setLoading(false);
    setAi(null);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (loading || over) return;
    if (empty) {
      // The button stays lit at rest; an empty press explains what to do instead of doing nothing.
      setError("Paste the text you received first, then press Check.");
      inputRef.current?.focus();
      return;
    }
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setLoading(true);
    setError(null);
    setAi(null);
    // Only when the user has opted in; runs in parallel and can never delay or alter the main result.
    if (aiConsent) {
      setAi({ status: "loading" });
      fetchContextual(text, ctrl.signal)
        .then((state) => { if (abortRef.current === ctrl) setAi(state); })
        .catch(() => { /* aborted */ });
    }
    try {
      setResult(await analyzeMessage(text, ctrl.signal));
    } catch (err) {
      if ((err as Error).name === "AbortError") return;
      setResult(null);
      setError(err instanceof AnalyzeError ? err.message : "Something went wrong. Try again.");
    } finally {
      if (abortRef.current === ctrl) setLoading(false);
    }
  }

  function loadExample(t: string) {
    cancelPending();
    setText(t);
    setResult(null);
    setError(null);
  }

  function reset() {
    cancelPending();
    setResult(null);
    setError(null);
    setText("");
    inputRef.current?.focus();
  }

  function edit(t: string) {
    setText(t);
    if (error) setError(null);
  }

  return { text, setText: edit, result, error, loading, aiConsent, setAiConsent, ai, inputRef, length, over, empty, submit, loadExample, reset };
}

export { MAX_CHARS };
