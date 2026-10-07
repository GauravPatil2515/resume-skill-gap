import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Check, X } from "lucide-react";
import type { AnalyzeResult } from "@/lib/types";

export function KeywordGaps({ result }: { result: AnalyzeResult }) {
  const { present_keywords, missing_keywords, jd_keyword_groups } = result;

  const groups = [
    { label: "Tools / Technologies", items: jd_keyword_groups.tools },
    { label: "Methods / Capabilities", items: jd_keyword_groups.methods },
    { label: "Competencies", items: jd_keyword_groups.competencies },
    { label: "Industry / Domain", items: jd_keyword_groups.industry },
  ];

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {/* Present vs Missing summary */}
      <div className="space-y-6">
        <Card className="border border-border shadow-clean bg-card">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold text-foreground">
              Matched Keywords ({present_keywords.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {present_keywords.length ? (
              <div className="flex flex-wrap gap-1.5">
                {present_keywords.map((k) => (
                  <Badge key={k} variant="accent" className="gap-1 text-xs py-1">
                    <Check className="h-3 w-3" /> {k}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">No matched keywords.</p>
            )}
          </CardContent>
        </Card>

        <Card className="border border-destructive/20 shadow-clean bg-card">
          <CardHeader className="pb-3">
            <CardTitle className="text-base font-semibold text-foreground">
              Missing Keywords ({missing_keywords.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {missing_keywords.length ? (
              <div className="flex flex-wrap gap-1.5">
                {missing_keywords.map((k) => (
                  <Badge key={k} variant="outline" className="gap-1 text-xs py-1 border-destructive/40 text-destructive">
                    <X className="h-3 w-3" /> {k}
                  </Badge>
                ))}
              </div>
            ) : (
              <p className="text-xs text-muted-foreground">No gaps detected.</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Categorized JD keyword groups */}
      <Card className="border border-border shadow-clean bg-card lg:col-span-2">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-foreground">
            Categorized Skill Breakdown
          </CardTitle>
          <p className="text-xs text-muted-foreground">
            Extracted terms from the job description grouped by category.
          </p>
        </CardHeader>
        <CardContent className="grid gap-5 sm:grid-cols-2">
          {groups.map((g) => (
            <div key={g.label} className="space-y-2">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                {g.label}
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {g.items.length ? (
                  g.items.map((it) => (
                    <Badge
                      key={it}
                      variant={present_keywords.includes(it) ? "accent" : "outline"}
                      className="text-xs py-0.5"
                    >
                      {it}
                    </Badge>
                  ))
                ) : (
                  <span className="text-xs text-muted-foreground">—</span>
                )}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}

