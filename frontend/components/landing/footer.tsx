export function Footer() {
  return (
    <footer className="border-t border-border py-6 bg-card text-muted-foreground text-xs">
      <div className="mx-auto max-w-5xl px-6 flex flex-col sm:flex-row items-center justify-between gap-2">
        <p>© {new Date().getFullYear()} ResuMatch — ATS Resume &amp; Skill Gap Analyzer</p>
        <p>TF-IDF &amp; Semantic Matching Engine</p>
      </div>
    </footer>
  );
}

