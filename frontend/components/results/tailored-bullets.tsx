import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Copy, Check } from "lucide-react";
import { useState } from "react";
import type { AnalyzeResult } from "@/lib/types";

export function TailoredBullets({ result }: { result: AnalyzeResult }) {
  const { suggestions } = result;
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    const text = suggestions.tailored_bullets.join("\n");
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* ignore */
    }
  };

  return (
    <Card className="border border-border shadow-clean bg-card">
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-3">
        <div>
          <CardTitle className="text-lg font-semibold text-foreground">
            Tailored Resume Bullets
          </CardTitle>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Suggested bullet points incorporating missing job description keywords.
          </p>
        </div>
        <button
          onClick={copy}
          className="flex items-center gap-1.5 rounded-md border border-border px-2.5 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground bg-background transition-clean"
        >
          {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
          {copied ? "Copied" : "Copy Bullets"}
        </button>
      </CardHeader>
      <CardContent className="space-y-4">
        {suggestions.missing_keywords.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground mr-1">
              Target Keywords:
            </span>
            {suggestions.missing_keywords.map((k) => (
              <Badge key={k} variant="outline" className="border-border text-xs py-0.5">
                {k}
              </Badge>
            ))}
          </div>
        )}

        <ul className="space-y-2">
          {suggestions.tailored_bullets.map((b, i) => (
            <li
              key={i}
              className="flex items-start gap-2.5 rounded-md border border-border bg-background p-3 text-sm leading-relaxed text-foreground"
            >
              <span className="mt-0.5 font-bold text-accent">•</span>
              <span className="capitalize">{b}</span>
            </li>
          ))}
        </ul>

        {suggestions.notes && (
          <p className="rounded-md border border-border bg-background px-3 py-2 text-xs text-muted-foreground">
            <span className="font-semibold text-foreground">Note:</span> {suggestions.notes}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

