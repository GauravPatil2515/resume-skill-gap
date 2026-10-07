import { Header } from "@/components/landing/header";
import { Footer } from "@/components/landing/footer";
import { Analyzer } from "@/components/analyzer";

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground font-sans">
      <Header />

      <main className="flex-1 pt-24 pb-16">
        <div className="mx-auto max-w-5xl px-6 lg:px-8">
          <div className="text-center mb-10">
            <h1 className="font-serif text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight text-foreground">
              Resume &amp; Skill Gap Analyzer
            </h1>
            <p className="mt-3 text-base sm:text-lg text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              Upload your resume PDF and paste a job description to identify missing skills,
              rank bullet relevance, and get targeted improvements.
            </p>
          </div>

          <Analyzer />
        </div>
      </main>

      <Footer />
    </div>
  );
}

