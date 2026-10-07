import Link from "next/link";
import { FileText } from "lucide-react";

export function Header() {
  return (
    <header className="sticky top-0 z-50 bg-background/95 backdrop-blur border-b border-border">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-3.5">
        <Link href="/" className="flex items-center gap-2 font-serif font-semibold text-lg text-foreground">
          <div className="flex h-7 w-7 items-center justify-center rounded bg-accent text-accent-foreground">
            <FileText className="h-4 w-4" />
          </div>
          <span>ResuMatch</span>
        </Link>
        <div className="text-xs font-medium text-muted-foreground">
          ATS Resume &amp; Skill Gap Analyzer
        </div>
      </div>
    </header>
  );
}

