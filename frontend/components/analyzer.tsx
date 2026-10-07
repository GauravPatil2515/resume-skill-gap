"use client";

import { useState, useRef } from "react";
import {
  UploadCloud,
  FileText,
  X,
  Loader2,
  AlertCircle,
  ArrowRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent } from "@/components/ui/card";
import { analyzeResume } from "@/lib/api";
import type { AnalyzeResult } from "@/lib/types";
import { FitScoreCards } from "@/components/results/fit-score-cards";
import { KeywordGaps } from "@/components/results/keyword-gaps";
import { EvidenceRanking } from "@/components/results/evidence-ranking";
import { TailoredBullets } from "@/components/results/tailored-bullets";
import { MakeEditsPrompt } from "@/components/results/make-edits-prompt";
import { ResultsSkeleton } from "@/components/results/results-skeleton";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

type Status = "idle" | "loading" | "done" | "error";

export function Analyzer() {
  const [resume, setResume] = useState<File | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [jdText, setJdText] = useState("");
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState("");
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [useLLM, setUseLLM] = useState(true);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const onFile = (f: File | null) => {
    if (f && f.type === "application/pdf") {
      setResume(f);
      setError("");
    } else if (f) {
      setError("Resume must be a PDF file.");
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    onFile(e.dataTransfer.files?.[0] ?? null);
  };

  const submit = async () => {
    if (!resume) {
      setError("Please upload your resume PDF.");
      return;
    }
    if (!jdText.trim()) {
      setError("Please paste the job description.");
      return;
    }
    setStatus("loading");
    setError("");
    try {
      const form = new FormData();
      form.append("resume", resume);
      form.append("jd_text", jdText);
      form.append("llm_enable", String(useLLM));
      const res = await analyzeResume(form);
      setResult(res);
      setStatus("done");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.");
      setStatus("error");
    }
  };

  return (
    <div className="space-y-8">
      <Card className="border border-border shadow-clean bg-card">
        <CardContent className="p-6">
          <div className="grid gap-6 md:grid-cols-2">
            {/* Resume uploader */}
            <div>
              <label className="mb-2 block text-sm font-medium text-foreground">
                Resume (PDF)
              </label>
              <div
                onDragOver={(e) => {
                  e.preventDefault();
                  setDragActive(true);
                }}
                onDragLeave={() => setDragActive(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={
                  "flex min-h-[160px] cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed px-4 py-6 text-center transition-clean " +
                  (dragActive
                    ? "border-accent bg-accent/5"
                    : "border-border hover:border-muted-foreground/50 bg-background/50")
                }
              >
                {resume ? (
                  <div className="flex items-center gap-3">
                    <FileText className="h-7 w-7 text-accent shrink-0" />
                    <div className="text-left min-w-0">
                      <p className="text-sm font-medium text-foreground truncate">{resume.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {(resume.size / 1024 / 1024).toFixed(1)} MB
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setResume(null);
                      }}
                      className="ml-2 rounded p-1 text-muted-foreground hover:text-destructive transition-clean"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                ) : (
                  <>
                    <UploadCloud className="h-7 w-7 text-muted-foreground mb-2" />
                    <p className="text-sm font-medium text-foreground">
                      Click or drag PDF resume here
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">Up to 10MB</p>
                  </>
                )}
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="application/pdf"
                  className="hidden"
                  onChange={(e) => onFile(e.target.files?.[0] ?? null)}
                />
              </div>
            </div>

            {/* JD textarea */}
            <div>
              <label className="mb-2 block text-sm font-medium text-foreground">
                Job Description
              </label>
              <Textarea
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                placeholder="Paste the full job description text here…"
                className="min-h-[160px] resize-y text-sm"
              />
            </div>
          </div>

          <div className="mt-6 flex flex-col items-center gap-4 sm:flex-row sm:justify-between border-t border-border pt-4">
            <label className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer">
              <input
                type="checkbox"
                checked={useLLM}
                onChange={(e) => setUseLLM(e.target.checked)}
                className="h-4 w-4 rounded border-border text-accent accent-accent"
              />
              Enable AI bullet recommendations
            </label>

            <Button
              onClick={submit}
              disabled={status === "loading"}
              className="bg-accent text-accent-foreground hover:bg-accent/90 gap-2 font-medium"
              size="lg"
            >
              {status === "loading" ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Running analysis…
                </>
              ) : (
                <>
                  Analyze Resume <ArrowRight className="h-4 w-4" />
                </>
              )}
            </Button>
          </div>

          {error && (
            <div className="mt-4 flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" />
              {error}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Results Workspace */}
      <div>
        {status === "loading" && <ResultsSkeleton />}

        {status === "done" && result && (
          <div className="space-y-6">
            <FitScoreCards result={result} />

            <Tabs defaultValue="gaps" className="w-full">
              <TabsList className="grid w-full grid-cols-2 md:grid-cols-4 h-auto p-1 bg-card border border-border rounded-lg">
                <TabsTrigger value="gaps" className="py-2 text-sm font-medium">Skill Gaps</TabsTrigger>
                <TabsTrigger value="evidence" className="py-2 text-sm font-medium">Evidence Ranking</TabsTrigger>
                <TabsTrigger value="bullets" className="py-2 text-sm font-medium">Tailored Bullets</TabsTrigger>
                <TabsTrigger value="prompt" className="py-2 text-sm font-medium">Make-Edits Prompt</TabsTrigger>
              </TabsList>

              <TabsContent value="gaps" className="mt-4">
                <KeywordGaps result={result} />
              </TabsContent>
              <TabsContent value="evidence" className="mt-4">
                <EvidenceRanking result={result} />
              </TabsContent>
              <TabsContent value="bullets" className="mt-4">
                <TailoredBullets result={result} />
              </TabsContent>
              <TabsContent value="prompt" className="mt-4">
                <MakeEditsPrompt prompt={result.make_edits_prompt} />
              </TabsContent>
            </Tabs>
          </div>
        )}
      </div>
    </div>
  );
}

