import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Wrench, FlaskConical, Layers, ArrowUpRight, MessageSquare } from "lucide-react";
import type { AnalyzeResult } from "@/lib/types";

function DimensionBar({
  label,
  icon: Icon,
  value,
}: {
  label: string;
  icon: React.ElementType;
  value: number;
}) {
  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-sm">
        <span className="flex items-center gap-2 font-medium text-foreground">
          <Icon className="h-4 w-4 text-accent" />
          {label}
        </span>
        <span className="font-semibold text-foreground">{value}/10</span>
      </div>
      <Progress value={value * 10} className="h-1.5" />
    </div>
  );
}

export function FitScoreCards({ result }: { result: AnalyzeResult }) {
  const d = result.fit_dimensions;
  const simple = result.simple_score;
  const adv = result.advanced_score;

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Multi-dimensional fit */}
      <Card className="border border-border shadow-clean bg-card">
        <CardHeader className="pb-4">
          <CardTitle className="text-lg font-semibold text-foreground">
            Multi-dimensional Fit
          </CardTitle>
          <p className="text-xs text-muted-foreground">
            Evaluates alignment across five key dimensions.
          </p>
        </CardHeader>
        <CardContent className="space-y-4">
          <DimensionBar label="Tools" icon={Wrench} value={d.tools_score} />
          <DimensionBar label="Methods" icon={FlaskConical} value={d.methods_score} />
          <DimensionBar label="Domain" icon={Layers} value={d.domain_score} />
          <DimensionBar label="Seniority" icon={ArrowUpRight} value={d.seniority_score} />
          <DimensionBar label="Communication" icon={MessageSquare} value={d.communication_score} />

          <div className="mt-4 flex items-center justify-between rounded-md border border-border bg-background px-4 py-2.5">
            <span className="text-sm font-medium text-foreground">Overall Fit Score</span>
            <span className="text-xl font-bold text-accent">
              {d.overall_score ? d.overall_score.toFixed(1) : "0.0"} / 10
            </span>
          </div>
          {d.notes && (
            <p className="text-xs text-muted-foreground">{d.notes}</p>
          )}
        </CardContent>
      </Card>

      {/* ATS scores */}
      <Card className="border border-border shadow-clean bg-card">
        <CardHeader className="pb-4">
          <CardTitle className="text-lg font-semibold text-foreground">ATS Coverage &amp; Similarity</CardTitle>
          <p className="text-xs text-muted-foreground">
            Keyword coverage and semantic similarity against the job description.
          </p>
        </CardHeader>
        <CardContent className="space-y-5">
          <div>
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium text-foreground">Simple score</span>
              <span className="font-semibold text-foreground">
                {simple.composite.toFixed(1)} / 100
              </span>
            </div>
            <Progress value={simple.composite} className="mt-2 h-2" />
            <p className="mt-1.5 text-xs text-muted-foreground">
              Keyword coverage ≈ {(simple.keyword_coverage * 100).toFixed(0)}% · TF-IDF
              cosine ≈ {simple.tfidf_cosine.toFixed(2)}
            </p>
          </div>

          <div>
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium text-foreground">Advanced score</span>
              <span className="font-semibold text-foreground">
                {adv.composite.toFixed(1)} / 100
              </span>
            </div>
            <Progress value={adv.composite} className="mt-2 h-2" />
            <p className="mt-1.5 text-xs text-muted-foreground">
              Weighted coverage {(adv.weighted_keyword_coverage * 100).toFixed(0)}%
              {adv.semantic_cosine != null
                ? ` · Semantic cosine ≈ ${adv.semantic_cosine.toFixed(2)}`
                : ""}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 pt-1">
            <div className="rounded-md border border-border bg-background px-3 py-2.5 text-center">
              <div className="text-xl font-bold text-accent">
                {result.present_keywords.length}
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">Matched Keywords</p>
            </div>
            <div className="rounded-md border border-border bg-background px-3 py-2.5 text-center">
              <div className="text-xl font-bold text-destructive">
                {result.missing_keywords.length}
              </div>
              <p className="text-xs text-muted-foreground mt-0.5">Missing Keywords</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

