# LLM utilities for resume suggestions and scoring
from __future__ import annotations

import json
import os
import re
from dataclasses import asdict, dataclass
from typing import Iterable, List, Optional, Sequence, Set

# Config-driven NLP backend helpers
from .nlp_backends import _CFG, _canon

# Lightweight parsing utilities
from .parse import extract_skills, tokenize_words
from .pdf_utils import normalize

# Load .env if available
try:
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    pass

# LiteLLM is optional for swapping providers by model name
try:
    import litellm  # type: ignore
except Exception:  # pragma: no cover
    litellm = None  # type: ignore


_MODEL_ALIASES = {
    "claude-3-5-sonnet-latest": "anthropic/claude-3-5-sonnet-20241022",
    "claude-3-sonnet-latest": "anthropic/claude-3-sonnet-20240229",
    "claude-3-haiku-latest": "anthropic/claude-3-haiku-20240307",
}
_FALLBACK_ANTHROPIC = [
    "anthropic/claude-3-5-sonnet-20241022",
    "anthropic/claude-3-5-haiku-20241022",
    "anthropic/claude-3-sonnet-20240229",
    "anthropic/claude-3-haiku-20240307",
]


def _resolve_model(name: str) -> str:
    return _MODEL_ALIASES.get(name, name)


@dataclass
class Suggestions:
    missing_keywords: List[str]
    tailored_bullets: List[str]
    notes: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["missing_keywords"] = sorted(d["missing_keywords"])
        d["tailored_bullets"] = [b.strip() for b in d["tailored_bullets"] if b.strip()]
        return d


@dataclass
class FitDimensions:
    tools_score: int
    methods_score: int
    domain_score: int
    seniority_score: int
    communication_score: int
    overall_score: float
    notes: str | None = None

    def to_dict(self) -> dict:
        return {
            "tools_score": int(self.tools_score),
            "methods_score": int(self.methods_score),
            "domain_score": int(self.domain_score),
            "seniority_score": int(self.seniority_score),
            "communication_score": int(self.communication_score),
            "overall_score": float(self.overall_score),
            "notes": (self.notes or "").strip(),
        }


def _json_only(s: str) -> dict:
    """
    Try to parse JSON; if the model returns prose + JSON, extract the JSON block.
    """
    s = s.strip()
    try:
        return json.loads(s)
    except Exception:
        pass
    m = re.search(r"\{.*\}", s, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return {}


def _have_any_llm_key() -> bool:
    return any(
        os.environ.get(k)
        for k in (
            "GROQ_API_KEY",
            "ANTHROPIC_API_KEY",
            "OPENAI_API_KEY",
            "GOOGLE_API_KEY",
            "GEMINI_API_KEY",
            "AZURE_OPENAI_API_KEY",
        )
    )


def _fallback_bullets(
    jd_text: str,
    resume_text: str,
    missing: Sequence[str],
    present: Sequence[str],
    max_bullets: int = 5,
) -> List[str]:
    """
    Deterministic, no-LLM bullet generator (keeps demo working without keys).
    Uses actual resume content and JD keywords for relevance.
    """
    from ats.nlp_backends import extract_jd_keywords

    missing_norm = [m for m in (normalize(x) for x in missing) if m]
    present_norm = [p for p in (normalize(x) for x in present) if p]

    # Get JD keyword groups for more targeted bullets
    jd_kw = extract_jd_keywords(jd_text)
    jd_tools = jd_kw.get("tools", [])[:5]
    jd_methods = jd_kw.get("methods", [])[:5]

    # Extract action verbs from resume for more authentic bullets
    resume_verbs = []
    action_verbs = {"built", "developed", "created", "designed", "implemented", "engineered", 
                    "optimized", "improved", "reduced", "increased", "automated", "led", 
                    "managed", "delivered", "launched", "architected", "deployed", "scaled"}
    for word in tokenize_words(resume_text.lower()):
        if word in action_verbs and word not in resume_verbs:
            resume_verbs.append(word)
    if not resume_verbs:
        resume_verbs = ["built", "developed", "implemented", "improved", "designed"]

    templates = [
        "{verb} {kw} workflows to automate repetitive tasks, cutting manual effort by ~30%.",
        "Built analytics in {kw} and documented a reusable pattern to speed up similar projects.",
        "Integrated {kw} into the existing stack (leveraging {present}) to improve reliability and visibility.",
        "Created dashboards/alerts around {kw} to surface KPIs and reduce time-to-insight.",
        "Up-skilled teammates with short how-to notes on {kw}, raising adoption across the team.",
        "Designed {kw} pipelines for scalable data processing and model training.",
        "Optimized {kw} performance, reducing latency by ~40% through caching and indexing.",
    ]

    bullets: List[str] = []
    
    # Prioritize missing keywords that are in JD tools/methods
    priority_missing = [kw for kw in missing_norm if kw in jd_tools or kw in jd_methods]
    other_missing = [kw for kw in missing_norm if kw not in priority_missing]
    ordered_missing = priority_missing + other_missing

    for i, kw in enumerate(ordered_missing[:max_bullets]):
        verb = resume_verbs[i % len(resume_verbs)]
        t = templates[i % len(templates)]
        bullets.append(
            t.format(kw=_canon(kw), present=", ".join(present_norm[:3]) or "current tools", verb=verb)
        )

    if not bullets:
        generic = [
            "Quantified impact (time saved, defects reduced); added metrics directly into resume bullets.",
            "Refactored code for readability and tests; introduced pre-commit (ruff/black) to keep quality high.",
            "Shipped a small Streamlit demo to showcase results with downloads (CSV/JSON) for stakeholders.",
            "Used TF-IDF similarity to align achievements with JD keywords; addressed gaps explicitly.",
            "Wrote clear runbooks so others could reproduce results end-to-end.",
        ]
        bullets.extend(generic[:max_bullets])

    return bullets


def _combine_vocab(vocab: Optional[Iterable[str]]) -> Set[str]:
    """
    Combine caller-provided vocab with config canonical skills.
    Everything normalized; empty-safe.
    """
    cfg = set(_CFG.canonical_skills or [])
    user = set(vocab or [])
    return {normalize(x) for x in (cfg | user) if x}


# Extra soft terms to drop in addition to _CFG.stopwords
_EXTRA_EXCLUDE: Set[str] = {
    "must",
    "required",
    "requirement",
    "preferred",
    "nice to have",
}


def _clean_terms(seq: Sequence[str]) -> List[str]:
    """
    Canonicalise via synonyms map, drop stopwords/junk from config (+ tiny extra),
    and dedupe while preserving order.
    """
    stop = set(_CFG.stopwords or []) | _EXTRA_EXCLUDE
    out: List[str] = []
    seen: Set[str] = set()
    for t in seq or []:
        nt = _canon(normalize(t))
        if not nt or nt in stop:
            continue
        if nt in seen:
            continue
        seen.add(nt)
        out.append(nt)
    return out


def suggest_resume_improvements(
    *,
    jd_text: str,
    resume_text: str,
    missing_keywords: Optional[Sequence[str]] = None,
    present_keywords: Optional[Sequence[str]] = None,
    vocab: Optional[Sequence[str]] = None,
    model: Optional[str] = None,
    enable_llm: Optional[bool] = None,
    max_bullets: int = 5,
) -> Suggestions:
    """
    Produce missing keywords + 3–5 tailored resume bullets.

    Alignment:
      - Stopwords come from _CFG.stopwords (centralised) + a tiny extra soft set.
      - Canonicalisation via _canon (synonyms -> canonical terms).
      - Vocab = _CFG.canonical_skills ∪ (vocab arg).
      - Multi-model fallback via LiteLLM; deterministic fallback if disabled/unavailable.
    """
    # Normalize inputs and derive missing/present sets
    vocab_set = _combine_vocab(vocab)

    if missing_keywords is None or present_keywords is None:
        jd_hits = extract_skills(jd_text, vocab_set)
        res_hits = extract_skills(resume_text, vocab_set)
        missing_set = jd_hits - res_hits
        present_set = jd_hits & res_hits
        missing_keywords = sorted(missing_set)
        present_keywords = sorted(present_set)

    missing_keywords = _clean_terms(missing_keywords or [])
    present_keywords = _clean_terms(present_keywords or [])

    # Determine whether to call an LLM
    if enable_llm is None:
        enable_llm = os.environ.get("LLM_ENABLE", "0").strip() not in {
            "",
            "0",
            "false",
            "False",
        }

    have_key = _have_any_llm_key()
    model_name = model or os.environ.get("LLM_MODEL") or "claude-3-haiku-latest"
    target = _resolve_model(model_name)

    # If LLM is disabled or unavailable, use deterministic fallback
    if not enable_llm or litellm is None or not have_key:
        return Suggestions(
            missing_keywords=list(missing_keywords),
            tailored_bullets=_fallback_bullets(
                jd_text, resume_text, missing_keywords, present_keywords, max_bullets
            ),
            notes="fallback",
        )

    # Build strict JSON-only prompt
    sys_prompt = (
        "You are an expert resume editor. "
        "Return ONLY compact JSON. No markdown. No comments. Keys: "
        '{"missing_keywords": [], "tailored_bullets": [], "notes": ""}. '
        "Bullets must be first-person-omitted, action-led, quant-or-impact oriented, "
        "≤24 words each, no secrets, no hallucinations."
    )

    user_prompt = f"""
Resume (truncated OK):
{resume_text[:6000]}

Job Description (truncated OK):
{jd_text[:6000]}

Known present keywords: {list(present_keywords or [])}
Known missing keywords: {list(missing_keywords or [])}

TASK:
1) Confirm/adjust the missing_keywords (only terms truly present in the JD; lowercase; avoid soft words).
2) Write {max_bullets} tailored resume bullets integrating missing keywords naturally (no stuffing).
3) Add a 1-line 'notes' field with the single best advice (≤18 words).

OUTPUT STRICT JSON ONLY:
{{"missing_keywords": ["..."], "tailored_bullets": ["..."], "notes": "..."}}
""".strip()

    # Try primary model, then Anthropic fallbacks
    candidates = [target]
    if target.startswith("anthropic/"):
        candidates += [m for m in _FALLBACK_ANTHROPIC if m != target]

    last_err: Optional[Exception] = None

    for m in candidates:
        try:
            resp = litellm.completion(  # type: ignore
                model=m,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.2,
                max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "500")),
            )
            content = resp["choices"][0]["message"]["content"]  # type: ignore
            data = _json_only(content)

            mk = data.get("missing_keywords") if isinstance(data, dict) else None
            tb = data.get("tailored_bullets") if isinstance(data, dict) else None
            notes = (
                data.get("notes") if isinstance(data, dict) else None
            ) or "Mirror the JD’s must-haves precisely."

            if not isinstance(mk, list) or not isinstance(tb, list):
                raise ValueError("LLM returned invalid schema")

            mk_clean = _clean_terms(mk)
            tb_clean = [t.strip() for t in tb if isinstance(t, str) and t.strip()][:max_bullets]

            if not tb_clean:
                tb_clean = _fallback_bullets(
                    jd_text,
                    resume_text,
                    missing_keywords,
                    present_keywords,
                    max_bullets,
                )

            return Suggestions(
                missing_keywords=list(sorted(set(mk_clean))),
                tailored_bullets=tb_clean,
                notes=notes,
            )

        except Exception as e:
            last_err = e
            continue

    # Final fallback if all models fail
    return Suggestions(
        missing_keywords=list(missing_keywords),
        tailored_bullets=_fallback_bullets(
            jd_text, resume_text, missing_keywords, present_keywords, max_bullets
        ),
        notes=f"fallback ({type(last_err).__name__ if last_err else 'unknown'})",
    )


def score_fit_dimensions(
    *,
    jd_text: str,
    resume_text: str,
    present_keywords: Sequence[str] | None = None,
    missing_keywords: Sequence[str] | None = None,
    model: str | None = None,
    enable_llm: bool | None = None,
) -> FitDimensions:
    """
    Rate JD–resume fit along multiple dimensions on a 0–10 scale:

      - tools_score
      - methods_score
      - domain_score
      - seniority_score
      - communication_score
      - overall_score (0–10 float)

    Falls back to a category-aware heuristic if LLM is disabled/unavailable.
    """
    from ats.nlp_backends import extract_jd_keywords

    present_clean = _clean_terms(present_keywords or [])
    missing_clean = _clean_terms(missing_keywords or [])

    total = len(set(present_clean) | set(missing_clean)) or 1
    coverage = len(set(present_clean)) / float(total)

    # Heuristic fallback when LLM is not used
    if enable_llm is None:
        enable_llm = os.environ.get("LLM_ENABLE", "0").strip() not in {
            "",
            "0",
            "false",
            "False",
        }

    if not enable_llm or litellm is None or not _have_any_llm_key():
        # Category-aware heuristic: compute coverage per JD keyword group
        jd_kw = extract_jd_keywords(jd_text)
        
        def cat_coverage(category: str) -> float:
            cat_terms = set(jd_kw.get(category, []))
            if not cat_terms:
                return coverage  # fallback to overall
            cat_present = cat_terms & set(present_clean)
            return len(cat_present) / len(cat_terms)

        tools_cov = cat_coverage("tools")
        methods_cov = cat_coverage("methods")
        domain_cov = cat_coverage("industry")
        
        # Map coverage (0-1) to score (1-10) with some spread
        def cov_to_score(cov: float, base: float = 2.0, scale: float = 8.0) -> int:
            return max(1, min(10, int(round(base + scale * cov))))

        tools_score = cov_to_score(tools_cov)
        methods_score = cov_to_score(methods_cov)
        domain_score = cov_to_score(domain_cov)
        
        # Seniority and communication use overall coverage with slight variation
        seniority_score = cov_to_score(coverage, base=1.5, scale=7.0)
        communication_score = cov_to_score(coverage, base=1.0, scale=7.0)
        
        overall = (tools_score + methods_score + domain_score + seniority_score + communication_score) / 5.0

        return FitDimensions(
            tools_score=tools_score,
            methods_score=methods_score,
            domain_score=domain_score,
            seniority_score=seniority_score,
            communication_score=communication_score,
            overall_score=float(round(overall, 1)),
            notes="Heuristic category-based scores (LLM disabled/unavailable).",
        )

    if model is not None:
        model_name = model
    else:
        model_name = os.environ.get("LLM_MODEL", "claude-3-haiku-latest") or "claude-3-haiku-latest"

    target = _resolve_model(model_name)

    sys_prompt = (
        "You are an ATS and hiring assistant. "
        "Given a job description and a candidate resume, you will rate the fit "
        "on five dimensions from 0–10 (integers) and an overall score (0–10 float). "
        "Be strict but fair; 7–8 is a good match; 9–10 is exceptional. "
        "Return STRICT JSON only."
    )

    user_prompt = f"""
JOB DESCRIPTION (may be truncated):
{jd_text[:6000]}

RESUME (may be truncated):
{resume_text[:6000]}

PRESENT KEYWORDS (already matched): {list(present_clean)}
MISSING KEYWORDS (from JD but not resume): {list(missing_clean)}

DIMENSIONS (all 0–10):
- tools_score: match on tools/technologies.
- methods_score: match on methods, techniques, and ways of working.
- domain_score: relevance of domain/industry experience.
- seniority_score: does the resume match the expected level (grad/junior/mid/senior).
- communication_score: clarity of impact, business value, stakeholder skills.
- overall_score: holistic fit across all of the above (float, 1 decimal).

OUTPUT STRICT JSON ONLY in this shape:
{{
  "tools_score": 0,
  "methods_score": 0,
  "domain_score": 0,
  "seniority_score": 0,
  "communication_score": 0,
  "overall_score": 0.0,
  "notes": "short guidance, <= 25 words"
}}
""".strip()

    try:
        resp = litellm.completion(  # type: ignore[call-arg]
            model=target,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "400")),
        )
        content = resp["choices"][0]["message"]["content"]  # type: ignore[index]
        data = _json_only(content)

        if not isinstance(data, dict):
            raise ValueError("LLM did not return a JSON object")

        def _int_field(key: str, default: int) -> int:
            try:
                v = int(data.get(key, default))
            except Exception:
                return default
            return max(0, min(10, v))

        def _float_field(key: str, default: float) -> float:
            try:
                v = float(data.get(key, default))
            except Exception:
                return default
            return max(0.0, min(10.0, v))

        fd = FitDimensions(
            tools_score=_int_field("tools_score", 0),
            methods_score=_int_field("methods_score", 0),
            domain_score=_int_field("domain_score", 0),
            seniority_score=_int_field("seniority_score", 0),
            communication_score=_int_field("communication_score", 0),
            overall_score=_float_field("overall_score", coverage * 10.0),
            notes=(str(data.get("notes", "")) or "").strip(),
        )
        return fd
    except Exception:
        base = max(1, min(10, int(round(2 + 8 * coverage))))
        return FitDimensions(
            tools_score=base,
            methods_score=base,
            domain_score=max(1, base - 1),
            seniority_score=base,
            communication_score=base,
            overall_score=float(base),
            notes="Heuristic fallback due to LLM error.",
        )
