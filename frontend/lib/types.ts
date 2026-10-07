export interface AnalyzeResult {
  fit_dimensions: {
    tools_score: number;
    methods_score: number;
    domain_score: number;
    seniority_score: number;
    communication_score: number;
    overall_score: number;
    notes: string;
  };
  simple_score: {
    keyword_coverage: number;
    tfidf_cosine: number;
    composite: number;
    missing_keywords: string[];
    present_keywords: string[];
    jd_skill_count: number;
    resume_skill_count: number;
  };
  advanced_score: {
    keyword_coverage: number;
    weighted_keyword_coverage: number;
    tfidf_cosine: number;
    semantic_cosine: number | null;
    recency_factor: number;
    composite: number;
    present_keywords: string[];
    missing_keywords: string[];
    jd_skill_count: number;
    resume_skill_count: number;
  };
  jd_keyword_groups: {
    tools: string[];
    methods: string[];
    competencies: string[];
    industry: string[];
  };
  present_keywords: string[];
  missing_keywords: string[];
  evidence: {
    all: { text: string; score: number }[];
    top: { text: string; score: number }[];
    bottom: { text: string; score: number }[];
  };
  suggestions: {
    missing_keywords: string[];
    tailored_bullets: string[];
    notes: string | null;
  };
  make_edits_prompt: string;
  jd_title: string | null;
  jd_seniority: string | null;
}

export interface AnalysisError {
  detail: string;
}
