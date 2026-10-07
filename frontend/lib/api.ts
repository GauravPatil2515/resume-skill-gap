import type { AnalyzeResult } from "./types";

/**
 * Calls the FastAPI analysis backend. In dev, requests are proxied through
 * Next.js rewrites (/api/analyze -> http://localhost:8000/analyze).
 */
export async function analyzeResume(form: FormData): Promise<AnalyzeResult> {
  const res = await fetch("/api/analyze", {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    let message = "Analysis failed. Please try again.";
    try {
      const err = await res.json();
      if (err?.detail) message = err.detail;
    } catch {
      /* ignore parse errors */
    }
    throw new Error(message);
  }

  return (await res.json()) as AnalyzeResult;
}
