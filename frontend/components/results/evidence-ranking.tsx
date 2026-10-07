import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle2, AlertCircle } from "lucide-react";
import type { AnalyzeResult } from "@/lib/types";

function BulletRow({
  text,
  score,
  tone,
}: {
  text: string;
  score: number;
  tone: "good" | "weak";
}) {
  return (
    <div className="flex items-start gap-2.5 rounded-md border border-border bg-background p-3 text-sm">
      {tone === "good" ? (
        <CheckCircle2 className="h-4 w-4 text-accent shrink-0 mt-0.5" />
      ) : (
        <AlertCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
      )}
      <div className="min-w-0 flex-1">
        <p className="leading-relaxed text-foreground">{text}</p>
      </div>
      <span className="shrink-0 text-xs font-medium text-muted-foreground">
        {(score * 100).toFixed(0)}%
      </span>
    </div>
  );
}

export function EvidenceRanking({ result }: { result: AnalyzeResult }) {
  const { top, bottom } = result.evidence;

  return (
    <div className="grid gap-6 md:grid-cols-2">
      <Card className="border border-border shadow-clean bg-card">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base font-semibold text-foreground">
            Top Matching Bullets
          </CardTitle>
          <p className="text-xs text-muted-foreground">Most relevant bullet points in your resume.</p>
        </CardHeader>
        <CardContent className="space-y-2.5">
          {top.length ? (
            top.map((b, i) => <BulletRow key={i} text={b.text} score={b.score} tone="good" />)
          ) : (
            <p className="py-4 text-center text-xs text-muted-foreground">No bullets detected.</p>
          )}
        </CardContent>
      </Card>

      <Card className="border border-border shadow-clean bg-card">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-base font-semibold text-foreground">
            Weakest Matching Bullets
          </CardTitle>
          <p className="text-xs text-muted-foreground">
            Lowest relevance — consider revising or replacing these.
          </p>
        </CardHeader>
        <CardContent className="space-y-2.5">
          {bottom.length ? (
            bottom
              .slice()
              .reverse()
              .map((b, i) => <BulletRow key={i} text={b.text} score={b.score} tone="weak" />)
          ) : (
            <p className="py-4 text-center text-xs text-muted-foreground">No bullets detected.</p>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

